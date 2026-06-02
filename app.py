import streamlit as st
import requests
import json

st.set_page_config(page_title="Ethical Brand Scanner", layout="wide")

st.markdown("##### 🇵🇸 **Stop the Genocide**")
st.markdown("### 🛡️ Ethical Brand & Product Scanner")

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
except KeyError:
    st.error("API keys not detected in Secrets.")
    st.stop()

# Execution
query = st.text_input("Enter Brand Name:")
if st.button("Analyze"):
    with st.spinner("Auditing..."):
        # Discovery
        payload = {"api_key": TAVILY_API_KEY, "query": f"parent company of {query} and ethical controversies", "search_depth": "advanced"}
        resp = requests.post("https://api.tavily.com/search", json=payload)
        
        context = "No context found."
        if resp.status_code == 200:
            res = resp.json()
            # STRICT CHECK: Ensure res is a dictionary
            if isinstance(res, dict):
                ans = res.get("answer", "")
                results = res.get("results", [])
                # Ensure results is a list
                if isinstance(results, list):
                    content_list = [r.get("content", "") for r in results if isinstance(r, dict)]
                    context = str(ans) + "\n" + "\n".join(content_list)
            else:
                st.error(f"Unexpected API format: {type(res)}")
                st.stop()

        # Audit
        prompt = "Analyze brand ethics. Return JSON only with 'status', 'summary', and 'breakdown' (1-10)."
        llm_payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": f"Brand: {query}\nContext: {context}"}],
            "response_format": {"type": "json_object"}
        }
        
        resp_llm = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                 headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=llm_payload)
        
        if resp_llm.status_code == 200:
            data = resp_llm.json()
            result = json.loads(data["choices"][0]["message"]["content"])
            st.write(f"**Status:** {result.get('status')}")
            st.write(f"**Summary:** {result.get('summary')}")
            st.json(result.get("breakdown"))
        else:
            st.error(f"Audit API Error: {resp_llm.text}")
