import streamlit as st
import pandas as pd
from backend import get_groq_client, process_query

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(page_title="AI Data Assistant", page_icon="🖥️", layout="wide", initial_sidebar_state="collapsed")

# --------------------------------------------------
# Design tokens & CSS  —  "Data Console" theme
# --------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg: #0B0F17;
        --surface: #121826;
        --surface-2: #1A2233;
        --border: #26324A;
        --text: #E7ECF3;
        --text-muted: #8B98AC;
        --accent: #FFB454;
        --accent-dim: #7A5A2A;
        --accent-2: #5FD3C4;
        --danger: #FF7A7A;
        --radius: 14px;
    }

    html, body, .stApp {
        background: radial-gradient(circle at 15% 0%, #101828 0%, var(--bg) 45%) fixed;
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }
    header, footer, #MainMenu {visibility: hidden;}

    h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
        color: var(--text) !important;
    }

    /* ---------- Hero header ---------- */
    .console-hero {
        display: flex; align-items: center; gap: 16px;
        padding: 6px 2px 22px 2px;
        border-bottom: 1px solid var(--border);
        margin-bottom: 26px;
    }
    .console-hero .dot { width: 10px; height: 10px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 12px var(--accent); animation: pulse 2.2s ease-in-out infinite; }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .35; } }
    .console-hero .title { font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 800; color: var(--text); margin: 0; }
    .console-hero .subtitle { font-family: 'Inter', sans-serif; font-size: 0.9rem; color: var(--text-muted); margin: 2px 0 0 0; }
    .console-hero .badge {
        margin-left: auto; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
        color: var(--accent-2); border: 1px solid var(--border); background: var(--surface-2);
        padding: 5px 10px; border-radius: 999px; letter-spacing: 0.04em;
    }

    /* ---------- Console panel (replaces bento-box) ---------- */
    .console-panel {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        margin-bottom: 20px;
        overflow: hidden;
        box-shadow: 0 8px 24px -12px rgba(0,0,0,0.5);
        animation: fadeInUp 0.35s ease both;
    }
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    .console-panel-bar {
        display: flex; align-items: center; gap: 8px;
        padding: 10px 16px; background: var(--surface-2);
        border-bottom: 1px solid var(--border);
    }
    .console-panel-bar .c { width: 9px; height: 9px; border-radius: 50%; }
    .console-panel-bar .c1 { background: #FF6159; } .console-panel-bar .c2 { background: #FFBD2E; } .console-panel-bar .c3 { background: #29C940; }
    .console-panel-bar .label {
        font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-muted);
        margin-left: 8px; letter-spacing: 0.03em; text-transform: uppercase;
    }
    .console-panel-body { padding: 18px 20px 20px 20px; }

    /* ---------- Metrics ---------- */
    [data-testid="stMetric"] {
        background: var(--surface-2); border: 1px solid var(--border); border-radius: 10px;
        padding: 12px 14px 8px 14px;
    }
    [data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.7rem !important; letter-spacing: 0.06em; text-transform: uppercase; }
    [data-testid="stMetricValue"] { color: var(--accent-2) !important; font-family: 'JetBrains Mono', monospace !important; font-weight: 700 !important; }

    /* ---------- File uploader ---------- */
    [data-testid="stFileUploaderDropzone"] {
        background: var(--surface-2) !important; border: 1.5px dashed var(--border) !important; border-radius: 10px !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover { border-color: var(--accent) !important; }
    [data-testid="stFileUploader"] section { color: var(--text-muted); }

    /* ---------- Chat bubbles ---------- */
    .chat-row { display: flex; margin-bottom: 12px; }
    .chat-row.user { justify-content: flex-end; }
    .chat-user {
        background: var(--accent-dim); color: #FFE9C7; border: 1px solid #4A3820;
        padding: 10px 14px; border-radius: 12px 12px 2px 12px; max-width: 78%;
        font-family: 'JetBrains Mono', monospace; font-size: 0.88rem;
    }
    .chat-user::before { content: "❯ "; color: var(--accent); font-weight: 700; }
    .chat-ai {
        background: var(--surface-2); border: 1px solid var(--border); color: var(--text);
        padding: 10px 14px; border-radius: 12px 12px 12px 2px; max-width: 86%;
        font-size: 0.92rem;
    }

    /* code blocks rendered inside chat-ai / markdown */
    .stMarkdown pre, pre {
        background: #0D1320 !important; border: 1px solid var(--border) !important;
        border-radius: 10px !important; padding: 12px 14px !important;
    }
    .stMarkdown code, code { font-family: 'JetBrains Mono', monospace !important; color: var(--accent-2) !important; }

    /* ---------- Dataframe ---------- */
    [data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }

    /* ---------- Chat input ---------- */
    [data-testid="stChatInput"] textarea {
        background: var(--surface-2) !important; color: var(--text) !important;
        border: 1px solid var(--border) !important; font-family: 'JetBrains Mono', monospace !important;
    }
    [data-testid="stChatInput"] { border-top: 1px solid var(--border) !important; background: var(--bg) !important; }

    /* ---------- Misc ---------- */
    .stAlert { border-radius: 10px !important; }
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 6px; }

    .empty-state { text-align: center; padding: 60px 20px; color: var(--text-muted); }
    .empty-state .glyph { font-size: 2.2rem; margin-bottom: 10px; }
    .empty-state .h { font-family: 'JetBrains Mono', monospace; color: var(--text); font-size: 1.05rem; margin-bottom: 6px; }
</style>
""", unsafe_allow_html=True)


def panel_open(label: str):
    """Render the terminal-style chrome bar that opens a console panel."""
    st.markdown(f"""
        <div class="console-panel">
            <div class="console-panel-bar">
                <span class="c c1"></span><span class="c c2"></span><span class="c c3"></span>
                <span class="label">{label}</span>
            </div>
            <div class="console-panel-body">
    """, unsafe_allow_html=True)


def panel_close():
    st.markdown("</div></div>", unsafe_allow_html=True)


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
st.markdown("""
<div class="console-hero">
    <span class="dot"></span>
    <div>
        <p class="title">AI Data Assistant</p>
        <p class="subtitle">Ask questions in plain English — get pandas code and results, instantly.</p>
    </div>
    <span class="badge">● groq / gpt-oss-120b</span>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    panel_open("1_data_source.csv")
    st.subheader("Data Source")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    panel_close()

if uploaded_file is not None:
    @st.cache_data
    def load_data(file): return pd.read_csv(file)

    df = load_data(uploaded_file)

    with col2:
        panel_open("dataset_overview")
        st.subheader("Dataset Overview")
        stat1, stat2, stat3 = st.columns(3)
        stat1.metric("Rows", f"{df.shape[0]:,}")
        stat2.metric("Columns", df.shape[1])
        stat3.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        panel_close()

    panel_open("query_console")
    st.subheader("Ask Questions")

    # Display Chat History
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-row user"><div class="chat-user">{message["content"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-row"><div class="chat-ai">{message["content"]}</div></div>', unsafe_allow_html=True)
            if "result" in message and message["result"] is not None:
                if isinstance(message["result"], (pd.DataFrame, pd.Series)):
                    st.dataframe(message["result"], use_container_width=True)
                else:
                    st.write(message["result"])

    panel_close()

    # Chat Input Trigger
    if prompt := st.chat_input("E.g., Show the top 2 products by sales"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
else:
    with col2:
        panel_open("awaiting_input")
        st.markdown("""
            <div class="empty-state">
                <div class="glyph">📊</div>
                <div class="h">No dataset loaded yet</div>
                <div>Upload a CSV on the left to see stats and start asking questions.</div>
            </div>
        """, unsafe_allow_html=True)
        panel_close()

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