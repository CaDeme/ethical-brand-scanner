import streamlit as st
import requests
import json

st.set_page_config(page_title="Ethical Brand Scanner", layout="centered")

# --- CSS ---
st.markdown("""
    <style>
        .stTextInput { text-align: center; }
        .main .block-container { max-width: 900px !important; }
    </style>
""", unsafe_allow_html=True)

# Restore Banner and Title
st.markdown("<h5 style='text-align: center;'>🇵🇸 Stop the Genocide</h5>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>🛡️ Ethical Brand & Product Scanner (Two-Stage)</h3>", unsafe_allow_html=True)

# --- State Initialization ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'context' not in st.session_state: st.session_state.context = ""

query = st.text_input("Enter Brand Name:", placeholder="e.g. Ole Henriksen")

if query:
    if st.session_state.step == 1:
        with st.spinner("Mapping corporate ecosystem..."):
            # STAGE 1: Discovery
            payload = {"api_key": st.secrets["TAVILY_API_KEY"], "query": f"Who is the ultimate parent company of {query}? List its major subsidiaries, retail operations in China/Israel, and alcohol/meat portfolio.", "search_depth": "advanced"}
            resp = requests.post("https://api.tavily.com/search", json=payload)
            st.session_state.context = str(resp.json())
            st.session_state.step = 2
            st.rerun()

    if st.session_state.step == 2:
        with st.spinner("Applying ethical audit..."):
            # STAGE 2: Audit
            prompt = """
            Audit the brand based on this context: {context}.
            Check against these 10 criteria:
            1. No animal testing/sales in China. 2. 100% vegan. 3. No honey/bee. 4. No meat. 5. No dairy. 6. No fish. 7. No alcohol beverages (not cosmetic). 8. No ties to Israel. 9. No public proof of vindictive behavior. 10. No sugary products (soda/candy).
            Return JSON ONLY: {'status': 'PASSED'/'FAILED', 'parent_company': '...', 'breakdown': {'Criterion 1': {'status': 'Pass/Fail', 'details': '...'}, ...}}
            """
            
            llm_payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": prompt.format(context=st.session_state.context)}, {"role": "user", "content": "Execute audit."}],
                "response_format": {"type": "json_object"}
            }
            
            resp_llm = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}, json=llm_payload)
            
            if resp_llm.status_code == 200:
                res = json.loads(resp_llm.json()["choices"][0]["message"]["content"])
                
                st.success(f"Audit Complete for: {query.upper()}")
                st.markdown(f"**Parent Company Identified:** {res.get('parent_company')}")
                
                table = "| Metric | Status | Finding |\n|:---|:---|:---|\n"
                for c, data in res.get("breakdown", {}).items():
                    icon = "🍏" if "pass" in str(data['status']).lower() else "🍎"
                    table += f"| {c} | {icon} | {data.get('details', 'N/A')} |\n"
                st.markdown(table)
                
                if st.button("New Scan"):
                    st.session_state.step = 1
                    st.rerun()
