import streamlit as st
import pandas as pd
from backend import get_groq_client, process_query

# --------------------------------------------------
# Page Configuration & CSS
# --------------------------------------------------
st.set_page_config(page_title="AI Data Assistant", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; color: #212529; }
    header, footer {visibility: hidden;}
    .bento-box {
        background-color: #FFFFFF; border-radius: 16px; padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px;
        border: 1px solid #E9ECEF;
    }
    .chat-user {
        background-color: #E9ECEF; padding: 12px 16px; border-radius: 12px 12px 0 12px;
        margin-bottom: 10px; max-width: 80%; margin-left: auto;
    }
    .chat-ai {
        background-color: #FFFFFF; border: 1px solid #DEE2E6; padding: 12px 16px;
        border-radius: 12px 12px 12px 0; margin-bottom: 10px; max-width: 80%;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Setup Backend State
# --------------------------------------------------
client = get_groq_client()

if not client:
    st.error("API Key file ('groq-api.key') not found in the directory. Please create it.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------------------------------
# UI Layout
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
    def load_data(file): return pd.read_csv(file)
    
    df = load_data(uploaded_file)
    
    with col2:
        st.markdown('<div class="bento-box">', unsafe_allow_html=True)
        st.subheader("Dataset Overview")
        stat1, stat2, stat3 = st.columns(3)
        stat1.metric("Rows", f"{df.shape[0]:,}")
        stat2.metric("Columns", df.shape[1])
        stat3.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="bento-box">', unsafe_allow_html=True)
    st.subheader("Ask Questions")
    
    # Display Chat History
    for message in st.session_state.messages:
        if message["role"] == "user":
             st.markdown(f'<div class="chat-user">{message["content"]}</div>', unsafe_allow_html=True)
        else:
             st.markdown(f'<div class="chat-ai">{message["content"]}</div>', unsafe_allow_html=True)
             if "result" in message and message["result"] is not None:
                 if isinstance(message["result"], (pd.DataFrame, pd.Series)):
                     st.dataframe(message["result"], use_container_width=True)
                 else:
                     st.write(message["result"])

    # Chat Input Trigger
    if prompt := st.chat_input("E.g., Show the top 2 products by sales"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

# --------------------------------------------------
# Process Chat Logic
# --------------------------------------------------
if uploaded_file is not None and st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_query = st.session_state.messages[-1]["content"]
    
    with st.spinner("Analyzing data..."):
        # Call external backend file
        code, result, error = process_query(client, df, user_query)
        
        if error:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"Failed to execute. Code attempted:\n```python\n{code}\n```",
                "result": f"**Error:** {error}"
            })
        else:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"**Generated Code:**\n```python\n{code}\n```",
                "result": result
            })
        st.rerun()