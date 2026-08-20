import streamlit as st
import pandas as pd
from backend import get_groq_client, process_query, generate_insights

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(page_title="Datalens", page_icon="🔍", layout="wide", initial_sidebar_state="collapsed")

# --------------------------------------------------
# Design tokens & CSS — "Red over Black" theme
# --------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700&display=swap');

    :root {
        --bg: #0A0A0A;
        --surface: #141414;
        --surface-2: #1C1C1C;
        --border: #2B2B2B;
        --text: #F2F2F2;
        --text-muted: #9C9C9C;

        --red: #E63946;
        --red-deep: #A61C2E;
        --red-bg: rgba(230, 57, 70, 0.12);
        --red-bg-strong: rgba(230, 57, 70, 0.20);
        --red-border: rgba(230, 57, 70, 0.40);
    }

    html, body, .stApp {
        background: var(--bg);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }
    header, footer, #MainMenu {visibility: hidden;}

    h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
        color: var(--text) !important;
    }

    /* ---------- Hero / brand mark : pinned to the top of the page ---------- */
    /* Streamlit's block container is what actually scrolls, so a sticky
       element inside it stays pinned to the top of the viewport instead of
       scrolling away with the rest of the content. */
    .hero-center {
        position: sticky;
        top: 0;
        z-index: 999;
        display: flex; flex-direction: column; align-items: center; text-align: center;
        gap: 12px; padding: 34px 0 34px 0;
        background: var(--bg);
        border-bottom: 1px solid var(--border);
        box-shadow: 0 12px 24px -14px rgba(0,0,0,0.75);
        margin: 0 0 28px 0;
    }
    .logo {
        font-family: 'Inter', sans-serif; font-weight: 900;
        font-size: clamp(3.5rem, 7vw, 7rem);
        letter-spacing: -0.03em; margin: 0; line-height: 1;
    }
    .logo .word-data { color: var(--red); }
    .logo .word-lens {
        color: #000000;
        -webkit-text-stroke: 2.6px var(--red);
        text-stroke: 2.6px var(--red);
        paint-order: stroke fill;
        text-shadow: -2px -2px 0 var(--red), 2px -2px 0 var(--red), -2px 2px 0 var(--red), 2px 2px 0 var(--red);
    }
    .tagline { font-size: 1.35rem; color: var(--text-muted); margin: 0; }
    .hero-badge {
        font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;
        color: var(--red); border: 1px solid var(--red-border); background: var(--red-bg);
        padding: 6px 14px; border-radius: 999px; letter-spacing: 0.04em; margin-top: 6px;
    }

    /* ---------- Panels: real bordered st.container ---------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        box-shadow: 0 10px 24px -16px rgba(0,0,0,0.7);
        margin-bottom: 20px;
    }

    .panel-tag {
        display: inline-flex; align-items: center; gap: 6px;
        font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; font-weight: 600;
        letter-spacing: 0.06em; text-transform: uppercase;
        padding: 4px 10px; border-radius: 6px; margin: -0.2rem 0 12px 0;
    }
    .panel-tag.red   { background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border); }
    .panel-tag.muted { background: var(--surface-2); color: var(--text-muted); border: 1px solid var(--border); }

    /* ---------- Section headings with icon badges (replaces emoji) ---------- */
    .icon-heading { display: flex; align-items: center; gap: 10px; margin: 0 0 12px 0; }
    .icon-badge {
        display: flex; align-items: center; justify-content: center;
        width: 32px; height: 32px; border-radius: 9px; flex-shrink: 0;
        background: var(--red-bg); border: 1px solid var(--red-border); color: var(--red);
    }
    .icon-badge svg { width: 18px; height: 18px; }
    .icon-heading .heading-text {
        font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1.25rem; color: var(--text);
    }

    /* ---------- Metrics ---------- */
    [data-testid="stMetric"] {
        background: var(--surface-2); border: 1px solid var(--border); border-radius: 10px;
        padding: 12px 14px 8px 14px;
    }
    [data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.68rem !important; letter-spacing: 0.06em; text-transform: uppercase; }
    [data-testid="stMetricValue"] { color: var(--red) !important; font-family: 'JetBrains Mono', monospace !important; font-weight: 700 !important; }

    /* ---------- File uploader ---------- */
    [data-testid="stFileUploaderDropzone"] {
        background: var(--surface-2) !important;
        border: 2px dashed var(--red-border) !important;
        border-radius: 12px !important;
        min-height: 190px !important;
        padding: 28px 20px !important;
        display: flex !important; flex-direction: column !important;
        align-items: center !important; justify-content: center !important;
        transition: border-color 0.15s ease, background 0.15s ease;
    }
    [data-testid="stFileUploaderDropzone"]:hover { border-color: var(--red) !important; background: var(--red-bg) !important; }
    [data-testid="stFileUploaderDropzone"] svg { width: 34px !important; height: 34px !important; color: var(--red) !important; }
    [data-testid="stFileUploaderDropzone"] section { color: var(--text-muted); }
    [data-testid="stFileUploaderDropzone"] span { font-size: 1rem !important; font-weight: 600 !important; color: var(--text) !important; }
    [data-testid="stFileUploaderDropzone"] small { font-size: 0.82rem !important; color: var(--text-muted) !important; }
    [data-testid="stFileUploaderDropzone"] button {
        margin-top: 10px !important; border: 1px solid var(--red-border) !important;
        background: var(--surface) !important; color: var(--red) !important;
        font-weight: 600 !important; padding: 8px 18px !important; border-radius: 8px !important;
    }
    [data-testid="stFileUploaderDropzone"] button:hover { background: var(--red-bg) !important; }

    /* ---------- Chat: rows + avatars ---------- */
    .chat-row { display: flex; align-items: flex-end; gap: 8px; margin-bottom: 14px; }
    .chat-row.user { justify-content: flex-end; }
    .chat-avatar {
        width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center;
        font-size: 15px; border: 1px solid var(--border);
    }
    .chat-avatar.ai   { background: var(--red-bg); border-color: var(--red-border); }
    .chat-avatar.user { background: var(--surface-2); }
    .chat-user {
        background: var(--red-bg); color: var(--text); border: 1px solid var(--red-border);
        padding: 10px 14px; border-radius: 12px 12px 2px 12px; max-width: 74%;
        font-size: 0.92rem;
    }
    .chat-ai {
        background: var(--surface-2); border: 1px solid var(--border); color: var(--text);
        padding: 10px 14px; border-radius: 12px 12px 12px 2px; max-width: 86%;
        font-size: 0.92rem;
    }
    .chat-ai.error { background: var(--red-bg-strong); border-color: var(--red-border); }

    /* code blocks (inside the code expander) */
    .stMarkdown pre, pre {
        background: var(--surface-2) !important; border: 1px solid var(--border) !important;
        border-radius: 10px !important; padding: 12px 14px !important;
    }
    .stMarkdown code, code { font-family: 'JetBrains Mono', monospace !important; color: var(--red) !important; }

    /* ---------- Expanders ---------- */
    [data-testid="stExpander"] {
        border: 1px solid var(--border) !important; border-radius: 10px !important;
        background: var(--surface-2) !important; margin-bottom: 8px;
    }
    [data-testid="stExpander"] summary { font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.88rem; color: var(--text); }

    /* ---------- Dataframe ---------- */
    [data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }

    /* ---------- Chat input ---------- */
    [data-testid="stChatInput"] textarea {
        background: var(--surface) !important; color: var(--text) !important;
        border: 1px solid var(--border) !important;
    }
    [data-testid="stChatInput"] { border-top: 1px solid var(--border) !important; background: var(--bg) !important; }

    /* ---------- Misc ---------- */
    .stAlert { border-radius: 10px !important; }
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 6px; }
</style>
""", unsafe_allow_html=True)


def panel_tag(label: str, variant: str = "red"):
    """Nameplate-style section label. Call as the first thing inside a
    `with st.container(border=True):` block so it's a real child of that panel."""
    st.markdown(f'<span class="panel-tag {variant}">{label}</span>', unsafe_allow_html=True)


ICON_LIGHTBULB = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
    stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/>
    <path d="M12 2a7 7 0 0 0-7 7c0 2.4 1.4 3.9 2.4 5.3.6.8 1.1 1.6 1.3 2.7h6.6c.2-1.1.7-1.9 1.3-2.7
    C17.6 12.9 19 11.4 19 9a7 7 0 0 0-7-7z"/></svg>"""

ICON_BAR_CHART = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
    stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M18 17V9"/>
    <path d="M13 17V5"/><path d="M8 17v-3"/></svg>"""


def icon_heading(icon_svg: str, text: str):
    """Section heading with a red-tinted icon badge, replacing emoji subheaders."""
    st.markdown(
        f'<div class="icon-heading"><span class="icon-badge">{icon_svg}</span>'
        f'<span class="heading-text">{text}</span></div>',
        unsafe_allow_html=True
    )


def format_compact(n: float) -> str:
    """Format a bin-edge number without ever falling back to scientific
    notation (unlike Python's `g` format), so distribution-chart axis
    labels stay human-readable (e.g. '5.40B' instead of '5.4e+09')."""
    if pd.isna(n):
        return "—"
    abs_n = abs(n)
    if abs_n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if abs_n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if abs_n >= 1_000:
        return f"{n / 1_000:.2f}K"
    if abs_n >= 1:
        return f"{n:.2f}"
    return f"{n:.4f}"


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
# Brand header
# --------------------------------------------------
st.markdown("""
<div class="hero-center">
    <p class="logo"><span class="word-data">Data</span><span class="word-lens">lens</span></p>
    <p class="tagline">Bring your data into focus.</p>
    <span class="hero-badge">● groq / gpt-oss-120b</span>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# File upload — full width until a file is loaded, then moves into
# the narrow left column alongside the rest of the layout.
# --------------------------------------------------
file_loaded = "file_name" in st.session_state

if not file_loaded:
    with st.container(border=True):
        panel_tag("Data Source", "red")
        st.subheader("Upload a file")
        uploaded_file = st.file_uploader(
            "Upload File", type=["csv", "xlsx", "xls"],
            label_visibility="collapsed", key="csv_uploader"
        )

    if uploaded_file is not None:
        st.session_state.file_name = uploaded_file.name
        st.session_state.pop("insights", None)
        st.session_state.messages = []
        st.rerun()
    else:
        st.stop()
else:
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.container(border=True):
            panel_tag("Data Source", "red")
            st.subheader("Upload a file")
            uploaded_file = st.file_uploader(
                "Upload File", type=["csv", "xlsx", "xls"],
                label_visibility="collapsed", key="csv_uploader"
            )

    if uploaded_file is None:
        # User cleared the uploaded file — fall back to the full-width prompt.
        st.session_state.pop("file_name", None)
        st.rerun()

    if st.session_state.file_name != uploaded_file.name:
        st.session_state.file_name = uploaded_file.name
        st.session_state.pop("insights", None)
        st.session_state.messages = []

    @st.cache_data
    def load_data(file):
        if file.name.endswith(".csv"):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)

    df = load_data(uploaded_file)

    with col2:
        with st.container(border=True):
            panel_tag("Dataset Overview", "red")
            st.subheader("Dataset Overview")
            stat1, stat2, stat3 = st.columns(3)
            stat1.metric("Rows", f"{df.shape[0]:,}")
            stat2.metric("Columns", df.shape[1])
            stat3.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    insight_col, dash_col = st.columns(2)

    with insight_col:
        with st.container(border=True):
            panel_tag("Business Insights", "red")
            icon_heading(ICON_LIGHTBULB, "Business Insights")
            if "insights" not in st.session_state:
                with st.spinner("Generating insights..."):
                    st.session_state.insights = generate_insights(client, df)
            st.markdown(st.session_state.insights.replace("$", "\\$"))

    with dash_col:
        with st.container(border=True):
            panel_tag("Automated Dashboard", "red")
            icon_heading(ICON_BAR_CHART, "Automated Dashboard")
            num_cols = df.select_dtypes(include=['number']).columns.tolist()
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

            if num_cols:
                st.markdown("**Numerical Distributions**")
                for col in num_cols[:2]:
                    with st.expander(f"View {col} distribution"):
                        counts = df[col].value_counts(bins=10).sort_index()
                        counts.index = counts.index.map(
                            lambda x: f"{format_compact(x.left)} – {format_compact(x.right)}"
                        )
                        st.bar_chart(counts)

            if cat_cols:
                st.markdown("**Categorical Counts**")
                for col in cat_cols[:2]:
                    if df[col].nunique() < 20:
                        with st.expander(f"View {col} counts"):
                            st.bar_chart(df[col].value_counts())

    with st.container(border=True):
        panel_tag("Query Console", "red")
        st.subheader("Ask Questions")

        # Display Chat History
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(
                    f'<div class="chat-row user"><div class="chat-user">{message["content"]}</div>'
                    f'<div class="chat-avatar user">🧑</div></div>',
                    unsafe_allow_html=True
                )
            else:
                bubble_class = "chat-ai error" if message.get("error") else "chat-ai"
                st.markdown(
                    f'<div class="chat-row"><div class="chat-avatar ai">🤖</div>'
                    f'<div class="{bubble_class}">{message["content"]}</div></div>',
                    unsafe_allow_html=True
                )
                if "result" in message and message["result"] is not None:
                    if isinstance(message["result"], (pd.DataFrame, pd.Series)):
                        st.dataframe(message["result"])
                    else:
                        st.write(message["result"])
                if message.get("code"):
                    with st.expander("🔍 View generated code"):
                        st.code(message["code"], language="python")

    # Chat Input Trigger
    if prompt := st.chat_input("E.g., Show the top 2 products by sales"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # --------------------------------------------------
    # Process Chat Logic
    # --------------------------------------------------
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        user_query = st.session_state.messages[-1]["content"]

        with st.spinner("Analyzing data..."):
            # Call external backend file
            code, result, error = process_query(client, df, user_query)

            if error:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Failed to execute this query. **Error:** {error}",
                    "result": None,
                    "code": code,
                    "error": True,
                })
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Here's what I found:",
                    "result": result,
                    "code": code,
                    "error": False,
                })
            st.rerun()