import streamlit as st
import requests
import json

# 1. Page Configuration
st.set_page_config(page_title="Ethical Brand Scanner", layout="wide")
st.markdown("##### 🇵🇸 **Stop the Genocide**")
st.markdown("### 🛡️ Ethical Brand & Product Scanner")

# 2. CSS Injection for Clean UI
st.html("""
    <style>
        div[data-testid="stForm"] { padding: 0.1rem !important; border: none !important; }
        .stTextInput div[data-baseweb="input"] { border-radius: 4px !important; }
        table { width: 100% !important; font-size: 12.5px !important; }
        th, td { padding: 3px 5px !important; line-height: 1.15 !important; }
    </style>
""")

# 3. Secure Key Retrieval (Reads from .streamlit/secrets.toml)
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
except KeyError:
    st.error("Missing keys. Please ensure .streamlit/secrets.toml is configured.")
    st.stop()

# 4. Master Prompt
CRITERIA_PROMPT = """
You are a forensic business analyst. Perform a two-step analysis.
STEP 1: CORPORATE DISCOVERY - Use the provided search results to identify the ultimate parent company. If the brand was acquired by a conglomerate (e.g., Unilever, L'Oréal, P&G) in the last 2 years, explicitly flag this.
STEP 2: ETHICAL EVALUATION - Audit the brand and its ULTIMATE PARENT against these 10 criteria:
1. No animal testing/No China sales. 2. 100% vegan ingredients. 3. No honey. 4. No meat. 5. No dairy. 6. No fish. 7. No alcohol. 8. No ties to Israel. 9. No harmful corporate behavior. 10. No sugary products.

OUTPUT: Return a valid JSON object ONLY.
{
    "status": "PASSED" or "FAILED",
    "summary": "Identify ultimate parent company and why it passed/failed.",
    "breakdown": {
        "Criterion 1": {"status": "Pass" or "Fail", "details": "..."},
        ... (1 to 10)
    }
}
"""

# 5. Execution
with st.form(key="search_form"):
    query = st.text_input("Enter Brand Name:", placeholder="e.g., Wild")
    submit = st.form_submit_button(label="Analyze")

if submit and query:
    with st.spinner(f"Forensically auditing '{query}'..."):
        # Forced Discovery Search
        tavily_payload = {
            "api_key": TAVILY_API_KEY,
            "query": f"Who is the ultimate parent company of {query}? Recent acquisitions by conglomerates? Ownership structure.",
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
        
        st.markdown(f"**Results for: {query.upper()}** | **Status: {result.get('status')}**")
        st.info(result.get('summary'))
        
        # Display Table
        table = "| Metric | Status | Details |\n| :--- | :--- | :--- |\n"
        for i in range(1, 11):
            crit = f"Criterion {i}"
            info = result["breakdown"].get(crit, {"status": "Fail", "details": "N/A"})
            table += f"| **{crit}** | {info['status']} | {info['details']} |\n"
        st.markdown(table)
