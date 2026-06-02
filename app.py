import streamlit as st
import requests
import json

# 1. Initialize ALL session state variables immediately
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'context' not in st.session_state:
    st.session_state.context = ""
if 'audit_result' not in st.session_state:
    st.session_state.audit_result = None

# UI Header
st.markdown("<h5 style='text-align: center;'>🇵🇸 Stop the Genocide</h5>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>🛡️ Ethical Brand & Product Scanner (Two-Stage)</h3>", unsafe_allow_html=True)

# Callback to reset the app
def reset_app():
    st.session_state.step = 1
    st.session_state.context = ""
    st.session_state.audit_result = None

# 2. Main Logic Pipeline
query = st.text_input("Enter Brand Name:", key="brand_input")

if query:
    if st.session_state.step == 1:
        with st.spinner("Mapping corporate ecosystem..."):
            try:
                payload = {
                    "api_key": st.secrets["TAVILY_API_KEY"], 
                    "query": f"Ultimate parent company of {query}, subsidiaries, China/Israel ties, alcohol/meat/dairy portfolio.", 
                    "search_depth": "advanced"
                }
                resp = requests.post("https://api.tavily.com/search", json=payload)
                st.session_state.context = str(resp.json())
                st.session_state.step = 2
                st.rerun() # Force rerun to move to stage 2
            except Exception as e:
                st.error(f"Mapping failed: {e}")

if st.session_state.step == 2 and st.session_state.context:
    with st.spinner("Applying ethical audit..."):
        try:
            prompt = """Audit the brand based on this context: {context}. 
            Apply your 10-point checklist. Return JSON only: {'status': 'PASSED'/'FAILED', 'parent_company': '...', 'breakdown': {...}}"""
            
            llm_payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": prompt.format(context=st.session_state.context)}, 
                    {"role": "user", "content": "Execute audit."}
                ],
                "response_format": {"type": "json_object"}
            }
            
            resp_llm = requests.post(
                "https://api.groq.com/openai/v1/chat/completions", 
                headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}, 
                json=llm_payload
            )
            
            if resp_llm.status_code == 200:
                st.session_state.audit_result = json.loads(resp_llm.json()["choices"][0]["message"]["content"])
                st.session_state.step = 3 # Move to display stage
                st.rerun()
        except Exception as e:
            st.error(f"Audit failed: {e}")

# 3. Display Stage
if st.session_state.step == 3 and st.session_state.audit_result:
    res = st.session_state.audit_result
    st.success(f"Audit Complete")
    st.write(f"**Parent Company Identified:** {res.get('parent_company')}")
    
    for c, data in res.get("breakdown", {}).items():
        icon = "🍏" if "pass" in str(data['status']).lower() else "🍎"
        st.write(f"{icon} **{c}**: {data.get('details', 'N/A')}")
        
    st.button("New Scan", on_click=reset_app)
