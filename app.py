import streamlit as st
import requests
import json

# Page Configuration
st.set_page_config(page_title="Ethical Brand Scanner", layout="centered")

# Centering & Layout CSS
st.markdown("""
    <style>
        .main .block-container { max-width: 900px !important; }
        .stTextInput { text-align: center; }
        table { width: 100% !important; font-size: 14px !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h5 style='text-align: center;'>🇵🇸 Stop the Genocide</h5>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>🛡️ Ethical Brand & Product Scanner</h3>", unsafe_allow_html=True)

# Load API keys
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
except KeyError:
    st.error("API keys not detected in Secrets.")
    st.stop()

CRITERIA_LIST = [
    ("Criterion 1", "No animal testing — no sales in China or anywhere testing is required"),
    ("Criterion 2", "100% vegan ingredients — no honey, beeswax, lanolin etc."),
    ("Criterion 3", "No honey or bee-derived products in the portfolio"),
    ("Criterion 4", "No meat products in the portfolio"),
    ("Criterion 5", "No dairy products in the portfolio"),
    ("Criterion 6", "No fish products in the portfolio"),
    ("Criterion 7", "No alcohol beverages in the portfolio (wine, beer, spirits — not cosmetic alcohol)"),
    ("Criterion 8", "No ties to Israel"),
    ("Criterion 9", "No documented public proof of vindictive or harmful behavior by parent company or investor toward founders or communities"),
    ("Criterion 10", "No sugary products in the portfolio (sodas, sweet beverages, candy, confectionery)")
]

# Search Input (Press Enter to trigger)
query = st.text_input("Enter Brand or Product Name:", placeholder="Type and press Enter...")

if query:
    with st.spinner("Auditing..."):
        # Discovery
        payload = {"api_key": TAVILY_API_KEY, "query": f"parent company of {query} and ethical controversies regarding china, israel, veganism, and alcohol", "search_depth": "advanced"}
        resp = requests.post("https://api.tavily.com/search", json=payload)
        context = ""
        if resp.status_code == 200 and isinstance(resp.json(), dict):
            context = str(resp.json().get("answer", "")) + "\n" + "\n".join([r.get("content", "") for r in resp.json().get("results", [])])

        # Audit
        prompt = "Return JSON exactly: {'parent_company': '...', 'status': 'PASSED'/'FAILED', 'summary': '...', 'breakdown': {'Criterion 1': {'status': 'Pass/Fail', 'details': '...'}, ...}}"
        llm_payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": f"Analyze: {query}\nContext: {context}"}],
            "response_format": {"type": "json_object"}
        }
        
        resp_llm = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=llm_payload)
        
        if resp_llm.status_code == 200:
            result = json.loads(resp_llm.json()["choices"][0]["message"]["content"])
            
            # Display Results
            status_display = "❌ FAILED CRITERIA" if "fail" in result.get("status", "").lower() else "🏆 PASSED"
            st.markdown(f"**Results for: {query.upper()} | Status: {status_display}**")
            st.markdown(f"**Corporate Context:** {result.get('parent_company', 'Unknown')} | {result.get('summary', '')}")
            
            # Criteria Table
            table = "| Metric | Status | Ethical Requirement | Audit Finding |\n|:---|:---|:---|:---|\n"
            for c_id, c_desc in CRITERIA_LIST:
                item = result.get("breakdown", {}).get(c_id, {"status": "Fail", "details": "N/A"})
                icon = "🍏 Pass" if "pass" in str(item['status']).lower() else "🍎 Fail"
                table += f"| **{c_id}** | {icon} | {c_desc} | {item.get('details', 'N/A')} |\n"
            st.markdown(table)
