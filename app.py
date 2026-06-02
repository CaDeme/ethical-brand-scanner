import streamlit as st
import requests
import json

# 1. Page Configuration
st.set_page_config(page_title="Ethical Brand Scanner", layout="wide")

# 2. BANNERS
st.markdown("##### 🇵🇸 **Stop the Genocide**")
st.markdown("### 🛡️ Ethical Brand & Product Scanner")

# 3. CSS Injection
st.html("""
    <style>
        div[data-testid="stForm"] { padding: 0.1rem !important; border: none !important; }
        .stTextInput div[data-baseweb="input"] { border-radius: 4px !important; }
        table { width: 100% !important; font-size: 12.5px !important; }
        th, td { padding: 3px 5px !important; line-height: 1.15 !important; }
    </style>
""")

# 4. Secure Key Retrieval
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
except KeyError as e:
    st.error(f"Missing configuration: {e}")
    st.stop()

# 5. Master Prompt
CRITERIA_PROMPT = """
You are a meticulous corporate auditor. Audit the brand against these 10 criteria:
1. No animal testing/No China sales. 2. 100% vegan ingredients. 3. No honey. 4. No meat. 5. No dairy. 6. No fish. 7. No alcohol. 8. No ties to Israel. 9. No harmful corporate behavior. 10. No sugary products.

Return JSON only:
{
    "status": "PASSED" or "FAILED",
    "summary": "Ultimate parent company and evaluation result.",
    "breakdown": {
        "Criterion 1": {"status": "Pass/Fail", "details": "..."},
        ... (repeat 1-10)
    }
}
"""

CRITERIA_DESCRIPTIONS = {
    f"Criterion {i}": desc for i, desc in enumerate([
        "No animal testing — no sales in China", "100% vegan ingredients",
        "No honey", "No meat", "No dairy", "No fish",
        "No alcohol beverages", "No ties to Israel",
        "No harmful behavior by parent company", "No sugary products"
    ], 1)
}

# 6. Execution
with st.form(key="search_form"):
    query = st.text_input("Enter Brand Name:", placeholder="Type brand name...")
    submit = st.form_submit_button(label="Analyze")

if submit and query:
    with st.spinner(f"Auditing '{query}'..."):
        # Discovery
        tavily_payload = {"api_key": TAVILY_API_KEY, "query": f"ultimate parent company of {query} and ethical controversies", "search_depth": "advanced"}
        resp_search = requests.post("https://api.tavily.com/search", json=tavily_payload)
        
        context = ""
        if resp_search.status_code == 200:
            res = resp_search.json()
            context = res.get("answer", "") + "\n" + "\n".join([r.get("content", "") for r in res.get("results", [])])
        else:
            st.error(f"Search API failed: {resp_search.text}")
            st.stop()

        # Audit
        llm_payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": CRITERIA_PROMPT}, {"role": "user", "content": f"Analyze: {query}\n\nContext:\n{context}"}],
            "response_format": {"type": "json_object"}
        }
        resp_audit = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                   headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=llm_payload)
        
        if resp_audit.status_code == 200:
            data = resp_audit.json()
            result = json.loads(data["choices"][0]["message"]["content"])
            
            st.markdown(f"**Results: {query.upper()}** | **Status: {result.get('status')}**")
            st.markdown(f"**Summary:** {result.get('summary')}")
            
            table = "| Metric | Status | Requirement | Finding |\n|---|---|---|---|\n"
            for i in range(1, 11):
                c = f"Criterion {i}"
                item = result["breakdown"].get(c, {"status": "Fail", "details": "N/A"})
                table += f"| **{c}** | {item['status']} | {CRITERIA_DESCRIPTIONS[c]} | {item['details']} |\n"
            st.markdown(table)
        else:
            st.error(f"Audit API failed: {resp_audit.text}")
