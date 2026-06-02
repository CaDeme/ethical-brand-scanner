import streamlit as st
import requests
import json

# 1. Initialize State
if 'step' not in st.session_state: st.session_state.step = 1
if 'context' not in st.session_state: st.session_state.context = ""
if 'audit_result' not in st.session_state: st.session_state.audit_result = None

st.set_page_config(page_title="Ethical Brand Scanner", layout="centered")

# UI Elements
st.markdown("<h5 style='text-align: center;'>🇵🇸 Stop the Genocide</h5>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>🛡️ Ethical Brand & Product Scanner</h3>", unsafe_allow_html=True)

def reset_app():
    st.session_state.step = 1
    st.session_state.context = ""
    st.session_state.audit_result = None

query = st.text_input("Enter Brand Name:")

# 2. Logic Pipeline
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
                st.rerun()
            except Exception as e:
                st.error(f"Mapping failed: {e}")

if st.session_state.step == 2 and st.session_state.context:
    with st.spinner("Applying ethical audit..."):
        prompt = """You are a strict JSON-only API. Audit the brand based on this context: {context}.
        Check against these 10 criteria. Return ONLY valid JSON with fields: 'status', 'parent_company', 'breakdown'."""
        try:
            llm_payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": prompt.format(context=st.session_state.context)}, {"role": "user", "content": "Execute audit."}],
                "response_format": {"type": "json_object"}
            }
            resp_llm = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}, json=llm_payload)
            
            if resp_llm.status_code == 200:
                content = resp_llm.json()["choices"][0]["message"]["content"]
                res = json.loads(content)
                if 'status' in res and 'breakdown' in res:
                    st.session_state.audit_result = res
                    st.session_state.step = 3
                    st.rerun()
                else:
                    st.error("Audit failed: Invalid JSON structure.")
        except Exception as e:
            st.error(f"Audit failed: {e}")

# 3. Display Result
if st.session_state.step == 3 and st.session_state.audit_result:
    res = st.session_state.audit_result
    st.success("Audit Complete")
    st.write(f"**Parent Company:** {res.get('parent_company', 'Unknown')}")
    
    # DEFENSIVE LOOP: Ensures 'data' is always a dictionary
    for criterion, data in res.get("breakdown", {}).items():
        if isinstance(data, dict):
            status_text = str(data.get('status', 'fail')).lower()
            icon = "🍏" if "pass" in status_text else "🍎"
            details = data.get('details', 'N/A')
            st.write(f"{icon} **{criterion}**: {details}")
        else:
            st.write(f"🍎 **{criterion}**: Data unavailable.")
            
    st.button("New Scan", on_click=reset_app)
