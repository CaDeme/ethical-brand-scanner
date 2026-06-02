import streamlit as st
import requests
import json

st.set_page_config(page_title="Ethical Brand Scanner", layout="centered")

# --- UI Header ---
st.markdown("<h5 style='text-align: center;'>🇵🇸 Stop the Genocide</h5>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>🛡️ Ethical Brand & Product Scanner (Two-Stage)</h3>", unsafe_allow_html=True)

# --- Robust Initialization ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'context' not in st.session_state: st.session_state.context = ""

query = st.text_input("Enter Brand Name:", placeholder="e.g. Ole Henriksen")

# --- Logic Pipeline ---
if query:
    if st.session_state.step == 1:
        with st.spinner("Mapping corporate ecosystem..."):
            payload = {"api_key": st.secrets["TAVILY_API_KEY"], "query": f"Ultimate parent company of {query}, subsidiaries, China/Israel ties, alcohol/meat/dairy portfolio.", "search_depth": "advanced"}
            resp = requests.post("https://api.tavily.com/search", json=payload)
            st.session_state.context = str(resp.json())
            st.session_state.step = 2
            st.rerun()

    # Use .get() to safely access context
    ctx = st.session_state.get('context', "")
    
    if st.session_state.step == 2 and ctx:
        with st.spinner("Applying ethical audit..."):
            prompt = """Audit the brand based on this context: {context}. 
            Apply your 10-point checklist. Return JSON only: {'status': 'PASSED'/'FAILED', 'parent_company': '...', 'breakdown': {...}}"""
            
            llm_payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": prompt.format(context=ctx)}, {"role": "user", "content": "Execute audit."}],
                "response_format": {"type": "json_object"}
            }
            
            resp_llm = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}, json=llm_payload)
            
            if resp_llm.status_code == 200:
                res = json.loads(resp_llm.json()["choices"][0]["message"]["content"])
                st.success(f"Audit Complete for: {query.upper()}")
                st.write(f"**Parent Company Identified:** {res.get('parent_company')}")
                
                # Render table
                for c, data in res.get("breakdown", {}).items():
                    st.write(f"{'🍏' if 'pass' in str(data['status']).lower() else '🍎'} **{c}**: {data.get('details', 'N/A')}")
                
                if st.button("New Scan"):
                    st.session_state.step = 1
                    st.session_state.context = ""
                    st.rerun()
