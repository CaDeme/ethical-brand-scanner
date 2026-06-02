import streamlit as st
import requests
import json

# 1. Page Configuration
st.set_page_config(page_title="Ethical Brand Scanner", layout="centered")

# 2. Centering & Layout CSS
st.markdown("""
    <style>
        .main .block-container { max-width: 800px !important; padding-top: 1rem !important; }
        .stTextInput { text-align: center; }
        table { width: 100% !important; font-size: 12px !important; }
        .reportview-container .main .block-container { display: flex; flex-direction: column; align-items: center; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h5 style='text-align: center;'>🇵🇸 Stop the Genocide</h5>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>🛡️ Ethical Brand & Product Scanner</h3>", unsafe_allow_html=True)

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
except KeyError:
    st.error("API keys not detected in Secrets.")
    st.stop()

CRITERIA_DESCRIPTIONS = {
    f"Criterion {i}": desc for i, desc in enumerate([
        "No animal testing/China", "100% vegan", "No honey", "No meat", 
        "No dairy", "No fish", "No alcohol", "No ties to Israel", 
        "No harmful behavior", "No sugary products"
    ], 1)
}

with st.form(key="search_input_form"):
    query = st.text_input("Enter Brand or Product Name:", placeholder="Type and press Enter...")
    submit_button = st.form_submit_button(label="Analyze")

if (submit_button or query) and query:
    with st.spinner("Auditing..."):
        # Discovery
        payload = {"api_key": TAVILY_API_KEY, "query": f"parent company of {query} and ethical controversies", "search_depth": "advanced"}
        resp = requests.post("https://api.tavily.com/search", json=payload)
        context = ""
        if resp.status_code == 200 and isinstance(resp.json(), dict):
            context = str(resp.json().get("answer", "")) + "\n" + "\n".join([r.get("content", "") for r in resp.json().get("results", [])])

        # Updated Prompt with Parent Company requirement
        prompt = """Return JSON exactly: {
            "parent_company": "Name of the ultimate parent company",
            "status": "PASSED" or "FAILED",
            "summary": "Brief analysis",
            "breakdown": {"Criterion 1": {"status": "Pass/Fail", "details": "..."}, ...}
        }"""
        
        llm_payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": f"Analyze: {query}\nContext: {context}"}],
            "response_format": {"type": "json_object"}
        }
        
        resp_llm = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=llm_payload)
        
        if resp_llm.status_code == 200:
            result = json.loads(resp_llm.json()["choices"][0]["message"]["content"])
            
            # Displaying Parent Company clearly
            st.markdown(f"**Results for: {query.upper()}**")
            st.markdown(f"**Parent Company:** {result.get('parent_company', 'Unknown')}")
            st.markdown(f"**Status:** {result.get('status')}")
            st.caption(f"**Context:** {result.get('summary')}")
            
            table = "| Metric | Status | Requirement | Finding |\n|:---|:---|:---|:---|\n"
            for i in range(1, 11):
                c = f"Criterion {i}"
                item = result.get("breakdown", {}).get(c, {"status": "Fail", "details": "N/A"})
                icon = "🍏" if "pass" in str(item['status']).lower() else "🍎"
                table += f"| **{c}** | {icon} | {CRITERIA_DESCRIPTIONS[c]} | {item['details']} |\n"
            st.markdown(table)
