import streamlit as st
import requests
import json

# --- 1. DEFENSIVE STATE INITIALIZATION ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'context' not in st.session_state: st.session_state.context = ""
if 'audit_result' not in st.session_state: st.session_state.audit_result = None

st.set_page_config(page_title="Ethical Brand Scanner", layout="centered")

# --- UI ELEMENTS ---
st.markdown("<h5 style='text-align: center;'>🇵🇸 Stop the Genocide</h5>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>🛡️ Ethical Brand & Product Scanner</h3>", unsafe_allow_html=True)

def reset_app():
    st.session_state.step = 1
    st.session_state.context = ""
    st.session_state.audit_result = None
    st.rerun()

query = st.text_input("Enter Brand Name:", key="brand_input")

# --- 2. LOGIC PIPELINE ---
if query:
    if st.session_state.step == 1:
        with st.spinner("Mapping corporate ecosystem..."):
            try:
                payload = {
                    "api_key": st.secrets["TAVILY_API_KEY"], 
                    "query": f"Analyze {query} corporate structure, parent company, and ethical footprint regarding animal testing, China, Israel, alcohol, meat, dairy, fish, and vindictive behavior.",
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
        You MUST evaluate these 10 criteria. If info is missing, use parent company reputation.
        1. No animal testing/no China. 2. 100% vegan. 3. No honey/bee. 4. No meat. 5. No dairy. 6. No fish. 
        7. No alcohol beverages (not cosmetic). 8. No ties to Israel. 9. No public proof of vindictive behavior. 10. No sugary products.
        Return ONLY valid JSON with fields: {"status": "PASSED/FAILED", "parent_company": "...", "breakdown": {"Criterion 1": {"status": "...", "details": "..."}, ...}}"""
        
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
                if 'breakdown' in res:
                    st.session_state.audit_result = res
                    st.session_state.step = 3
                    st.rerun()
                else:
                    st.error("Audit failed: Invalid JSON structure.")
        except Exception as e:
            st.error(f"Audit failed: {e}")

# --- 3. DISPLAY RESULT ---
if st.session_state.step == 3 and st.session_state.audit_result:
    res = st.session_state.audit_result
    if not isinstance(res, dict) or "breakdown" not in res:
        st.error("Audit failed: The model returned an invalid format.")
        st.button("Retry", on_click=reset_app)
    else:
        st.success("Audit Complete")
        st.write(f"**Parent Company:** {res.get('parent_company', 'Unknown')}")
        
        for i in range(1, 11):
            c_key = f"Criterion {i}"
            data = res.get("breakdown", {}).get(c_key, {"status": "Fail", "details": "No data found."})
            
            if isinstance(data, dict):
                status_text = str(data.get('status', 'fail')).lower()
                icon = "🍏" if "pass" in status_text else "🍎"
                details = data.get('details', 'No evidence provided.')
                st.write(f"{icon} **{c_key}**: {details}")
            else:
                st.write(f"🍎 **{c_key}**: Data format error.")
            
        st.button("New Scan", on_click=reset_app)
