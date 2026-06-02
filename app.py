import streamlit as st
import requests
import json

# 1. Page Configuration
st.set_page_config(page_title="Ethical Brand Scanner", layout="wide")

st.markdown("##### 🇵🇸 **Stop the Genocide**")
st.markdown("### 🛡️ Ethical Brand & Product Scanner")

# 2. CSS Injection
st.html(
    """
    <style>
        div[data-testid="stForm"] { padding: 0.1rem !important; margin-bottom: 0.2rem !important; border: none !important; }
        div[data-testid="stFormHint"] { display: none !important; }
        .stTextInput div[data-baseweb="input"] { border-radius: 4px !important; }
        div[data-testid="stFormSubmitButton"] { display: none !important; }
        table { width: 100% !important; font-size: 12.5px !important; }
        th, td { padding: 3px 5px !important; line-height: 1.15 !important; }
    </style>
    """
)

# 3. Master Prompt with mandatory Discovery Step
CRITERIA_PROMPT = """
You are a forensic business analyst. You MUST perform a two-step analysis on the provided brand.

STEP 1: CORPORATE DISCOVERY
Analyze the provided search records to identify:
- Who is the absolute ultimate parent company? (Trace all subsidiaries up to the top conglomerate).
- Has there been a recent acquisition by a major conglomerate (Unilever, L'Oréal, P&G, LVMH, etc.)?

STEP 2: ETHICAL EVALUATION
Evaluate the brand and its ULTIMATE PARENT COMPANY against these 10 criteria:
1. No animal testing — no sales in China or markets requiring testing.
2. 100% vegan ingredients — no honey, beeswax, lanolin.
3. No honey/bee-derived products in the entire corporate portfolio.
4. No meat products in the entire corporate portfolio.
5. No dairy products in the entire corporate portfolio.
6. No fish products in the entire corporate portfolio.
7. No alcoholic beverages in the corporate portfolio.
8. No ties to Israel (investments, operations, or footprint).
9. No documented harmful/vindictive behavior by parent company toward founders/communities.
10. No sugary products/confectionery in the corporate portfolio.

OUTPUT: Valid JSON only.
{
    "status": "PASSED" or "FAILED",
    "summary": "State the ultimate parent company clearly and why it passed/failed.",
    "breakdown": {
        "Criterion 1": {"status": "Pass" or "Fail", "details": "..."},
        ... (10 criteria)
    }
}
"""

CRITERIA_DESCRIPTIONS = {
    "Criterion 1": "No animal testing / No China sales",
    "Criterion 2": "100% vegan ingredients",
    "Criterion 3": "No honey in portfolio",
    "Criterion 4": "No meat in portfolio",
    "Criterion 5": "No dairy in portfolio",
    "Criterion 6": "No fish in portfolio",
    "Criterion 7": "No alcohol in portfolio",
    "Criterion 8": "No ties to Israel",
    "Criterion 9": "No harmful corporate behavior",
    "Criterion 10": "No sugary products"
}

# 4. Sidebar Inputs
st.sidebar.header("Configuration")
api_key = st.secrets.get("GROQ_API_KEY", st.sidebar.text_input("Groq API Key:", type="password"))
tavily_key = st.sidebar.text_input("Tavily API Key (Required for accuracy):", type="password")

# 5. Search & Analysis Execution
with st.form(key="search_form"):
    query = st.text_input("Enter Brand Name:", placeholder="e.g., Wild")
    submit_button = st.form_submit_button(label="Analyze")

if submit_button and query:
    if not api_key or not tavily_key:
        st.error("Please provide both API Keys.")
    else:
        with st.spinner(f"Forensically auditing '{query}'..."):
            # Step 1: Force Ownership Discovery Search
            search_payload = {
                "api_key": tavily_key,
                "query": f"Who is the ultimate parent company of {query}? Has {query} been acquired by a conglomerate like Unilever or L'Oreal? Recent acquisition news.",
                "search_depth": "advanced"
            }
            search_res = requests.post("https://api.tavily.com/search", json=search_payload).json()
            search_context = search_res.get("answer", "") + "\n" + "\n".join([r["content"] for r in search_res.get("results", [])])

            # Step 2: LLM Audit
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": CRITERIA_PROMPT},
                    {"role": "user", "content": f"Analyze: {query}\n\nSearch records for corporate ownership:\n{search_context}"}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.0
            }
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                     headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, 
                                     json=payload).json()
            
            result = json.loads(response["choices"][0]["message"]["content"])
            
            # Display Results
            st.markdown(f"**Results for: {query.upper()}** | **Status: {result.get('status')}**")
            st.info(result.get('summary'))
            
            table_markdown = "| Metric | Status | Requirement | Details |\n| :--- | :--- | :--- | :--- |\n"
            for i in range(1, 11):
                crit = f"Criterion {i}"
                info = result["breakdown"].get(crit, {"status": "Fail", "details": "N/A"})
                table_markdown += f"| **{crit}** | {info['status']} | {CRITERIA_DESCRIPTIONS[crit]} | {info['details']} |\n"
            st.markdown(table_markdown)
