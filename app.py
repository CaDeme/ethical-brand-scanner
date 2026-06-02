import streamlit as st
import requests
import json

st.set_page_config(page_title="Ethical Brand Scanner (Pro)", layout="centered")

# --- CSS for clean layout ---
st.markdown("""
    <style>
        .stTextInput { text-align: center; }
        .main { background-color: #f9f9f9; }
        .audit-box { background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center;'>🛡️ Ethical Brand & Product Scanner (Two-Stage)</h3>", unsafe_allow_html=True)

# --- State Management ---
if 'step' not in st.session_state: st.session_state.step = 1

query = st.text_input("Enter Brand Name:", placeholder="e.g. Ole Henriksen")

if query and st.session_state.step == 1:
    with st.spinner("Mapping corporate ecosystem..."):
        # STAGE 1: Discover the entity
        payload = {"api_key": st.secrets["TAVILY_API_KEY"], "query": f"Who is the ultimate parent company of {query}? List its major subsidiaries, retail operations in China/Israel, and alcohol/meat portfolio.", "search_depth": "advanced"}
        resp = requests.post("https://api.tavily.com/search", json=payload)
        context = str(resp.json())
        
        # Save context for stage 2
        st.session_state.context = context
        st.session_state.step = 2

if st.session_state.step == 2:
    with st.spinner("Applying ethical audit..."):
        # STAGE 2: Rigorous Audit based on Stage 1 context
        prompt = """
        Audit the brand based on this company map: {context}.
        Check against these 10 criteria:
        1. No animal testing/sales in China.
        2. 100% vegan ingredients.
        3. No honey/bee products.
        4. No meat products.
        5. No dairy.
        6. No fish.
        7. No alcohol beverages (not cosmetic).
        8. No ties to Israel.
        9. No public proof of vindictive behavior.
        10. No sugary products (soda/candy).
        
        Return JSON ONLY: {'status': 'PASSED'/'FAILED', 'parent_company': '...', 'breakdown': {'Criterion 1': {'status': 'Pass/Fail', 'details': '...'}, ...}}
        """
        
        # Call LLM with the mapped context
        llm_payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": prompt.format(context=st.session_state.context)}, {"role": "user", "content": "Execute audit."}],
            "response_format": {"type": "json_object"}
        }
        
        resp_llm = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}, json=llm_payload)
        
        if resp_llm.status_code == 200:
            res = json.loads(resp_llm.json()["choices"][0]["message"]["content"])
            
            # Display results
            st.success(f"Audit Complete for: {query.upper()}")
            st.markdown(f"**Parent Company Identified:** {res.get('parent_company')}")
            st.markdown(f"### Status: {res.get('status')}")
            
            # Show Table
            table = "| Metric | Status | Finding |\n|:---|:---|:---|\n"
            for c, data in res.get("breakdown", {}).items():
                icon = "🍏" if "pass" in str(data['status']).lower() else "🍎"
                table += f"| {c} | {icon} | {data['details']} |\n"
            st.markdown(table)
            
            # Reset
            if st.button("New Scan"): st.session_state.step = 1
