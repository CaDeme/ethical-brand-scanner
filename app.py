import streamlit as st
import requests
import json

# [Keep your existing Page Configuration and CSS Injection here]

CRITERIA_PROMPT = """
You are a meticulous, highly accurate corporate auditor. 
CRITICAL RULE: You must perform a deep-dive analysis on the brand and its parent company.
If the provided 'search_context' does not clearly prove a brand's ownership or fails 
to provide information on the 10 criteria, you MUST output 'FAILED' for the status 
and explicitly state in the summary: 'Insufficient live data to verify corporate ethics.'

[... Keep your 10-point criteria list here ...]

OUTPUT FORMAT: Valid JSON only.
"""

# [Keep CRITERIA_DESCRIPTIONS here]

st.sidebar.header("Configuration")
api_key = st.secrets.get("GROQ_API_KEY", st.sidebar.text_input("Groq API Key:", type="password"))
tavily_key = st.sidebar.text_input("Tavily API Key (Required for Audit):", type="password")

with st.form(key="search_form"):
    query = st.text_input("Enter Brand Name:")
    submit_button = st.form_submit_button(label="Analyze")

if submit_button and query:
    if not api_key or not tavily_key:
        st.error("Both API keys are required for a verified audit.")
    else:
        with st.spinner(f"Verifying '{query}'..."):
            # 1. LIVE SEARCH STEP
            search_url = "https://api.tavily.com/search"
            payload = {
                "api_key": tavily_key,
                "query": f"{query} brand ownership parent company ethical audit 2026",
                "search_depth": "advanced"
            }
            search_res = requests.post(search_url, json=payload).json()
            search_context = search_res.get("answer", "") + "\n" + "\n".join([r["content"] for r in search_res.get("results", [])])

            # 2. AI AUDIT STEP
            audit_payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": CRITERIA_PROMPT},
                    {"role": "user", "content": f"Analyze: {query}. Search Evidence: {search_context}"}
                ],
                "response_format": {"type": "json_object"}
            }
            # [Add your headers and request logic here]
            # ... process result and display table ...
