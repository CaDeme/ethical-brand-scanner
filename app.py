import streamlit as st
import requests
import json

# 1. Page Configuration
st.set_page_config(page_title="Ethical Brand Scanner", layout="wide")
st.markdown("### 🛡️ Ethical Brand & Product Scanner")

# 2. Secure Key Retrieval (Accesses cloud secrets)
# This will look for keys in your Streamlit Cloud 'Secrets' settings
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
except KeyError:
    st.error("API keys not detected. Please configure them in Streamlit Cloud Secrets.")
    st.stop()

# 3. Master Prompt (unchanged core logic)
CRITERIA_PROMPT = """
You are a forensic business analyst. Perform a two-step analysis.
STEP 1: CORPORATE DISCOVERY - Use the provided search results to identify the ultimate parent company. 
STEP 2: ETHICAL EVALUATION - Audit the brand and its ULTIMATE PARENT against the 10-point checklist.
Return valid JSON only.
"""

# 4. Execution
with st.form(key="search_form"):
    query = st.text_input("Enter Brand Name:", placeholder="e.g., Wild")
    submit = st.form_submit_button(label="Analyze")

if submit and query:
    with st.spinner(f"Forensically auditing '{query}'..."):
        # Forced Discovery Search
        tavily_payload = {
            "api_key": TAVILY_API_KEY,
            "query": f"Who is the ultimate parent company of {query}? Recent acquisitions/ownership status.",
            "search_depth": "advanced"
        }
        search_res = requests.post("https://api.tavily.com/search", json=tavily_payload).json()
        context = search_res.get("answer", "") + "\n" + "\n".join([r["content"] for r in search_res.get("results", [])])

        # LLM Audit
        llm_payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": CRITERIA_PROMPT},
                {"role": "user", "content": f"Analyze: {query}\n\nOwnership context:\n{context}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=llm_payload).json()
        
        result = json.loads(response["choices"][0]["message"]["content"])
        st.info(result.get('summary'))
