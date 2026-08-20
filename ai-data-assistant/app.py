import streamlit as st
import pandas as pd
from groq import Groq
import os

# --------------------------------------------------
# Page Configuration & Zento-Inspired CSS
# --------------------------------------------------
st.set_page_config(page_title="AI Data Assistant", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp {
        background-color: #F8F9FA;
        color: #212529;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .bento-box {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        border: 1px solid #E9ECEF;
    }
    
    .chat-user {
        background-color: #E9ECEF;
        padding: 12px 16px;
        border-radius: 12px 12px 0px 12px;
        margin-bottom: 10px;
        max-width: 80%;
        margin-left: auto;
    }
    .chat-ai {
        background-color: #FFFFFF;
        border: 1px solid #DEE2E6;
        padding: 12px 16px;
        border-radius: 12px 12px 12px 0px;
        margin-bottom: 10px;
        max-width: 80%;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Initialization & Logic
# --------------------------------------------------
@st.cache_resource
def get_groq_client():
    try:
        with open("groq-api.key") as f:
             api_key = f.read().strip()
        return Groq(api_key=api_key)
    except FileNotFoundError:
        st.error("API Key file ('groq-api.key') not found in the directory.")
        return None

client = get_groq_client()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------------------------------
# UI Layout (Bento Grid Style)
# --------------------------------------------------
st.title("AI Data Assistant")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="bento-box">', unsafe_allow_html=True)
    st.subheader("1. Data Source")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file is not None:
    @st.cache_data
    def load_data(file):
        return pd.read_csv(file)
    
    df = load_data(uploaded_file)
    
    with col2:
        st.markdown('<div class="bento-box">', unsafe_allow_html=True)
        st.subheader("Dataset Overview")
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        stat_col1.metric("Rows", f"{df.shape[0]:,}")
        stat_col2.metric("Columns", df.shape[1])
        stat_col3.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="bento-box">', unsafe_allow_html=True)
    st.subheader("Data Preview")
    st.dataframe(df.head(5), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="bento-box">', unsafe_allow_html=True)
    st.subheader("Ask Questions")
    
    for message in st.session_state.messages:
        if message["role"] == "user":
             st.markdown(f'<div class="chat-user">{message["content"]}</div>', unsafe_allow_html=True)
        else:
             st.markdown(f'<div class="chat-ai">{message["content"]}</div>', unsafe_allow_html=True)
             if "result" in message:
                 if isinstance(message["result"], pd.DataFrame) or isinstance(message["result"], pd.Series):
                     st.dataframe(message["result"], use_container_width=True)
                 else:
                     st.write(message["result"])

    if prompt := st.chat_input("E.g., Show the top 2 products by sales"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

if uploaded_file is not None and st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_query = st.session_state.messages[-1]["content"]
    
    if client:
        with st.spinner("Analyzing data..."):
            llm_prompt = f"""
            You are an expert Python data analyst.
            A pandas dataframe called df is already loaded.
            
            Columns: {list(df.columns)}
            Data Types: {df.dtypes.to_dict()}
            
            Generate ONLY executable Python Pandas code.
            
            Rules:
            1. Return ONLY Python code. No markdown formatting like ```python.
            2. No explanation.
            3. Store final output in a variable named `result`.
            4. Use dataframe `df`.
            
            Question: {user_query}
            """
            
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": llm_prompt}],
                    temperature=0,
                )
                
                code = response.choices[0].message.content.strip()
                code = code.replace("```python", "").replace("```", "").strip()
                
                local_vars = {"df": df}
                exec(code, {}, local_vars)
                
                execution_result = local_vars.get("result", "Error: Variable 'result' not found.")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"**Generated Code:**\n```python\n{code}\n```",
                    "result": execution_result
                })
                st.rerun()
                
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"Failed to execute code.",
                    "result": f"Error: {str(e)}"
                })
                st.rerun()