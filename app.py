import streamlit as st
import requests
import json

st.set_page_config(page_title="Ethical Brand Scanner", layout="wide")

st.markdown("##### 🇵🇸 **Stop the Genocide**")
st.markdown("### 🛡️ Ethical Brand & Product Scanner")

# Load API keys from secrets
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
except KeyError:
    st.error("API keys not detected in Secrets.")
    st.stop()

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

query = st.text_input("Enter Brand or Product Name:")
if st.button("Analyze") and query:
    with st.spinner("Auditing..."):
        # Discovery
        payload = {"api_key": TAVILY_API_KEY, "query": f"Parent company of {query}? Acquisitions? Ethical controversies regarding China, Israel, veganism, and subsidiaries.", "search_depth": "advanced"}
        resp = requests.post("https://api.tavily.com/search", json=payload)
        context = ""
        if resp.status_code == 200:
            res = resp.json()
            if isinstance(res, dict):
                context = str(res.get("answer", "")) + "\n" + "\n".join([r.get("content", "") for r in res.get("results", [])])

        # Audit
        prompt = """Audit against 10 criteria: 1. No animal testing/China. 2. 100% vegan. 3. No honey. 4. No meat. 5. No dairy. 6. No fish. 7. No alcohol. 8. No ties to Israel. 9. No harmful behavior. 10. No sugary products.
        Return JSON exactly: {"status": "PASSED" or "FAILED", "summary": "...", "breakdown": {"Criterion 1": {"status": "Pass/Fail", "details": "..."}, ...}}"""
        
        llm_payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": f"Analyze: {query}\nContext: {context}"}],
            "response_format": {"type": "json_object"}
        }
        
        resp_llm = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=llm_payload)
        
        if resp_llm.status_code == 200:
            result = json.loads(resp_llm.json()["choices"][0]["message"]["content"])
            status_display = "🏆 GOLD STANDARD PASSED" if result.get("status") == "PASSED" else "❌ FAILED CRITERIA"
            st.markdown(f"**Results for: {query.upper()} | Status: {status_display}**")
            st.markdown(f"**Corporate Context:** {result.get('summary')}")
            
            # Recreate the table
            table = "| Metric | Status | Ethical Requirement | Audit Finding |\n| :--- | :--- | :--- | :--- |\n"
            for i in range(1, 11):
                c = f"Criterion {i}"
                item = result["breakdown"].get(c, {"status": "Fail", "details": "N/A"})
                icon = "🍏 Pass" if "pass" in item['status'].lower() else "🍎 Fail"
                table += f"| **{c}** | {icon} | {CRITERIA_DESCRIPTIONS[c]} | {item['details']} |\n"
            st.markdown(table)
        else:
            st.error("Audit API call failed.")
