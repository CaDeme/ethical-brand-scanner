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
except KeyError:
    st.error("API keys not detected. Please configure them in Streamlit Cloud Secrets.")
    st.stop()

# 5. Master Prompt
CRITERIA_PROMPT = """
You are a meticulous corporate auditor. Perform a two-step analysis.
STEP 1: CORPORATE DISCOVERY - Identify the ultimate parent company. If the brand was acquired by a conglomerate (e.g., Unilever, L'Oréal, P&G) in the last 2 years, explicitly flag this.
STEP 2: ETHICAL EVALUATION - Audit the brand and its ULTIMATE PARENT against these 10 criteria:
1. No animal testing/No China sales. 2. 100% vegan ingredients. 3. No honey. 4. No meat. 5. No dairy. 6. No fish. 7. No alcohol. 8. No ties to Israel. 9. No harmful corporate behavior. 10. No sugary products.

OUTPUT: Return a valid JSON object ONLY.
{
    "status": "PASSED" or "FAILED",
    "summary": "State the ultimate parent company clearly and why it passed/failed.",
    "breakdown": {
        "Criterion 1": {"status": "Pass" or "Fail", "details": "..."},
        "Criterion 2": {"status": "Pass" or "Fail", "details": "..."},
        "Criterion 3": {"status": "Pass" or "Fail", "details": "..."},
        "Criterion 4": {"status": "Pass" or "Fail", "details": "..."},
        "Criterion 5": {"status": "Pass" or "Fail", "details": "..."},
        "Criterion 6": {"status": "Pass" or "Fail", "details": "..."},
        "Criterion 7": {"status": "Pass" or "Fail", "details": "..."},
        "Criterion 8": {"status": "Pass" or "Fail", "details": "..."},
        "Criterion 9": {"status": "Pass" or "Fail", "details": "..."},
        "Criterion 10": {"status": "Pass" or "Fail", "details": "..."}
    }
}
"""

CRITERIA_DESCRIPTIONS = {
    "Criterion 1": "No animal testing — no sales in China or anywhere testing is required",
    "Criterion 2": "100% vegan ingredients — no honey, beeswax, lanolin etc.",
    "Criterion 3": "No honey or bee-derived products in the portfolio",
    "Criterion 4": "No meat products in the portfolio",
    "Criterion 5": "No dairy products in the portfolio",
    "Criterion 6": "No fish products in the portfolio",
    "Criterion 7": "No alcohol beverages in the portfolio (wine, beer, spirits — not cosmetic alcohol)",
    "Criterion 8": "No ties to Israel",
    "Criterion 9": "No documented public proof of vindictive or harmful behavior by parent company or investor toward founders or communities",
    "Criterion 10": "No sugary products in the portfolio (sodas, sweet beverages, candy, confectionery)"
}

# 6. Execution
with st.form(key="search_form"):
    query = st.text_input("Enter Brand Name:", placeholder="Type brand name and press Enter...")
    submit = st.form_submit_button(label="Analyze")

if submit and query:
    with st.spinner(f"Auditing '{query}'..."):
        # Live Discovery Search
        tavily_payload = {
            "api_key": TAVILY_API_KEY,
            "query": f"Who is the ultimate parent company of {query}? Recent acquisitions by conglomerates? Ownership structure and ethical controversies.",
            "search_depth": "advanced"
        }
        
        try:
            resp_search = requests.post("https://api.tavily.com/search", json=tavily_payload)
            if resp_search.status_code == 200:
                search_res = resp_search.json()
                context = search_res.get("answer", "") + "\n" + "\n".join([r.get("content", "") for r in search_res.get("results", [])])
            else:
                context = "Search data unavailable."
        except Exception:
            context = "Search service error."

        # AI Audit
        llm_payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": CRITERIA_PROMPT},
                {"role": "user", "content": f"Analyze: {query}\n\nOwnership context:\n{context}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        
        try:
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                     headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=llm_payload)
            response_data = response.json()
            
            if "error" in response_data:
                st.error(f"API Error: {response_data['error'].get('message', 'Unknown error')}")
            else:
                content = response_data["choices"][0]["message"]["content"]
                result = json.loads(content)
                
                status_text = "🏆 GOLD STANDARD PASSED" if result.get("status") == "PASSED" else "❌ FAILED CRITERIA"
                st.markdown(f"**Results for: {query.upper()}** | **Status: {status_text}**")
                st.markdown(f"**Corporate Context:** {result.get('summary', '')}")
                
                table = "| Metric | Status | Ethical Requirement | Audit Finding |\n| :--- | :--- | :--- | :--- |\n"
                for i in range(1, 11):
                    crit = f"Criterion {i}"
                    info = result["breakdown"].get(crit, {"status": "Fail", "details": "N/A"})
                    status_icon = "🍏 Pass" if info['status'].strip().lower() in ['pass', 'passed'] else "🍎 Fail"
                    table += f"| **{crit}** | {status_icon} | {CRITERIA_DESCRIPTIONS[crit]} | {info['details']} |\n"
                st.markdown(table)
        except Exception as e:
            st.error(f"Execution Error: {e}")
