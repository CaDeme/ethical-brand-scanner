import streamlit as st
st.image("TINY.jpg", width=300)
import requests
import json

# Master ethical criteria prompt
CRITERIA_PROMPT = """
You are a strict ethical brand auditor. Analyze the brand or product provided by the user and evaluate it against the following 10 distinct criteria. 

CRITERIA:
1. No animal testing (Cruelty-free).
2. No animal-derived ingredients (100% Vegan portfolio).
3. No links to geopolitical entities undergoing active humanitarian boycott.
4. Independent ownership (No massive multinational conglomerates like Nestlé, Unilever, L'Oréal, Procter & Gamble, Estée Lauder, Johnson & Johnson, Coty, Shiseido, Beiersdorf, or LVMH).
5. Production and sourcing outside of China.
6. Portfolio must be free of alcoholic beverage production (wine, beer, spirits). Cosmetic alcohol in formulas is acceptable.
7. Avoidance of large-scale e-commerce dominance platforms.
8. Focus on transparent, independent supply chains.
9. No documented public proof of vindictive or harmful behavior toward founders.
10. No sugary products like sodas or candy in the portfolio.

OUTPUT FORMAT:
You must respond with a valid JSON object ONLY. Do not include any conversational text outside the JSON.
{
    "status": "PASSED" or "FAILED",
    "summary": "A concise corporate context overview explaining ownership and ecosystem.",
    "breakdown": {
        "Criterion 1": {"status": "Pass" or "Fail", "details": "Explanation"},
        "Criterion 2": {"status": "Pass" or "Fail", "details": "Explanation"},
        "Criterion 3": {"status": "Pass" or "Fail", "details": "Explanation"},
        "Criterion 4": {"status": "Pass" or "Fail", "details": "Explanation"},
        "Criterion 5": {"status": "Pass" or "Fail", "details": "Explanation"},
        "Criterion 6": {"status": "Pass" or "Fail", "details": "Explanation"},
        "Criterion 7": {"status": "Pass" or "Fail", "details": "Explanation"},
        "Criterion 8": {"status": "Pass" or "Fail", "details": "Explanation"},
        "Criterion 9": {"status": "Pass" or "Fail", "details": "Explanation"},
        "Criterion 10": {"status": "Pass" or "Fail", "details": "Explanation"}
    }
}
"""

st.set_page_config(page_title="Ethical Brand Scanner", layout="centered")

st.title("🛡️ Ethical Brand & Product Scanner")
st.write("Evaluate brands and parent companies against strict ethical criteria completely for free.")

# Check for hidden deployment key first, otherwise look for sidebar input
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.sidebar.header("Configuration")
    api_key = st.sidebar.text_input("Enter your Groq API Key (gsk_...):", type="password")

query = st.text_input("Enter Brand or Product Name:", placeholder="e.g., BABYLISS, PINK")

if st.button("Analyze Brand"):
    if not api_key:
        st.error("Please provide a Groq API Key to proceed.")
    elif not query:
        st.warning("Please enter a brand name to analyze.")
    else:
        with st.spinner(f"Auditing '{query}' and its corporate ecosystem..."):
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": CRITERIA_PROMPT},
                        {"role": "user", "content": f"Analyze the following brand/product: {query}"}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                }
                
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                response_data = response.json()
                
                if "error" in response_data:
                    st.error(f"API Error: {response_data['error']['message']}")
                else:
                    result = json.loads(response_data["choices"][0]["message"]["content"])
                    
                    st.markdown("---")
                    st.header(f"Results for: {query}")
                    
                    if result.get("status") == "PASSED":
                        st.success("🏆 **STATUS: GOLD STANDARD PASSED**")
                    else:
                        st.error("❌ **STATUS: FAILED CRITERIA**")
                    
                    st.subheader("Corporate Context")
                    st.write(result.get("summary", "No corporate summary provided."))
                    
                    st.subheader("Detailed Checklist Breakdown")
                    breakdown = result.get("breakdown", {})
                    for criterion, info in breakdown.items():
                        with st.expander(f"{criterion}: {'✅ Pass' if info['status'] == 'Pass' else '❌ Fail'}"):
                            st.write(info.get("details", ""))
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
