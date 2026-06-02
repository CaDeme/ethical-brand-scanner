import streamlit as st
import requests
import json

# 1. Page Configuration
st.set_page_config(page_title="Ethical Brand Scanner", layout="wide")

# 2. FIXED STATIC HEADERS
st.markdown("##### 🇵🇸 **Stop the Genocide**")
st.markdown("### 🛡️ Ethical Brand & Product Scanner")

# 3. CSS Layout Injection
st.html(
    """
    <style>
        div[data-testid="stForm"] { padding: 0.1rem !important; margin-bottom: 0.2rem !important; border: none !important; }
        div[data-testid="stFormHint"] { display: none !important; }
        .stTextInput div[data-baseweb="input"] { border-radius: 4px !important; }
        div[data-testid="stFormSubmitButton"] { display: none !important; }
        table { width: 100% !important; font-size: 12.5px !important; }
        th, td { padding: 3px 5px !important; line-height: 1.15 !important; }
        hr { margin: 0.2rem 0 !important; }
        p, span { margin-bottom: 1px !important; }
    </style>
    """
)

# Your Master Prompt
CRITERIA_PROMPT = """You are a meticulous, highly accurate corporate auditor and brand researcher. Your task is to evaluate a brand and its entire corporate ecosystem against a strict 10-point ethical checklist.
Evaluate both the specific brand AND its parent company/entire corporate ecosystem against these 10 rules:
1. No animal testing/No China sales. 2. 100% vegan ingredients. 3. No honey/bee. 4. No meat. 5. No dairy. 6. No fish. 7. No alcohol beverages (not cosmetic). 8. No ties to Israel. 9. No vindictive behavior. 10. No sugary products.
Keep explanations precise (under 12 words per row).
OUTPUT FORMAT: JSON ONLY.
{"status": "PASSED" or "FAILED", "summary": "...", "breakdown": {"Criterion 1": {"status": "Pass/Fail", "details": "..."}, ...}}"""

CRITERIA_DESCRIPTIONS = {
    "Criterion 1": "No animal testing — no sales in China or anywhere testing is required",
    "Criterion 2": "100% vegan ingredients — no honey, beeswax, lanolin etc.",
    "Criterion 3": "No honey or bee-derived products in the portfolio",
    "Criterion 4": "No meat products in the portfolio",
    "Criterion 5": "No dairy products in the portfolio",
    "Criterion 6": "No fish products in the portfolio",
    "Criterion 7": "No alcohol beverages in the portfolio (wine, beer, spirits — not cosmetic alcohol)",
    "Criterion 8": "No ties to Israel",
    "Criterion 9": "No documented public proof of vindictive or harmful behavior",
    "Criterion 10": "No sugary products in the portfolio"
}

st.sidebar.header("Configuration")
api_key = st.secrets["GROQ_API_KEY"] if "GROQ_API_KEY" in st.secrets else st.sidebar.text_input("Enter Groq API Key:", type="password")
tavily_key = st.sidebar.text_input("Enter Tavily API Key:", type="password")

with st.form(key="search_form"):
    query = st.text_input("Enter Brand Name:", placeholder="Type brand name and press Enter...")
    submit_button = st.form_submit_button(label="Analyze")

if submit_button and query:
    if not api_key:
        st.error("Please provide a Groq API Key.")
    else:
        with st.spinner(f"Auditing '{query}'..."):
            try:
                # Direct API Call Flow
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": CRITERIA_PROMPT},
                        {"role": "user", "content": f"Analyze: {query}"}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.0
                }
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                       headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, 
                                       json=payload)
                
                response_data = response.json()
                
                if "choices" in response_data:
                    result = json.loads(response_data["choices"][0]["message"]["content"])
                    
                    status_text = "🏆 GOLD STANDARD PASSED" if result.get("status") == "PASSED" else "❌ FAILED CRITERIA"
                    st.markdown(f"**Results for: {query.upper()}** | **Status: {status_text}**")
                    st.markdown(f"**Corporate Context:** {result.get('summary', '')}")
                    
                    table_markdown = "| Metric | Status | Ethical Requirement | Audit Finding |\n| :--- | :--- | :--- | :--- |\n"
                    breakdown = result.get("breakdown", {})
                    
                    for i in range(1, 11):
                        criterion = f"Criterion {i}"
                        info = breakdown.get(criterion, {"status": "Fail", "details": "N/A"})
                        status_icon = "🍏 Pass" if str(info['status']).lower() == 'pass' else "🍎 Fail"
                        table_markdown += f"| **{criterion}** | {status_icon} | {CRITERIA_DESCRIPTIONS[criterion]} | {info.get('details', '')} |\n"
                    
                    st.markdown(table_markdown)
                else:
                    st.error("Audit returned no valid response. Check API key or query.")
            except Exception as e:
                st.error(f"Audit processing error: {e}")
