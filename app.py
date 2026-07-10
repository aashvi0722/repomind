import streamlit as st

from ingest import clone_repo, collect_python_files
from chunker import chunk_repo
from embed_store import build_collection
from qa import answer_question

st.set_page_config(page_title="RepoMind", page_icon="🧠", layout="wide")

# --- Custom styling: explicit containers, each with its own palette color ---
# page background   -> #001244 (navy-deep)
# hero container    -> #005086 (blue-mid)
# info/banner card  -> #f7d6bf (peach)
# sidebar panel     -> #318fb5 (blue-light)
# sage (#b0cac7)    -> used for borders/dividers tying the cards together
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

    :root {
        --navy-deep: #001244;
        --blue-mid: #005086;
        --blue-light: #318fb5;
        --sage: #b0cac7;
        --peach: #f7d6bf;
    }

    .stApp {
        background-color: var(--navy-deep);
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        padding-top: 2.5rem;
    }

    /* Sidebar = its own solid blue-light panel */
    section[data-testid="stSidebar"] {
        background-color: var(--blue-light);
        border-right: 3px solid var(--navy-deep);
    }
    section[data-testid="stSidebar"] h2 {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--navy-deep);
        font-size: 1.05rem;
        border-bottom: 2px solid var(--navy-deep);
        padding-bottom: 0.5rem;
    }
    section[data-testid="stSidebar"] label {
        color: var(--navy-deep) !important;
        font-weight: 700 !important;
    }

    /* Hero card: blue-mid container sitting on the navy page */
    .hero-card {
        background-color: var(--blue-mid);
        border-radius: 16px;
        padding: 2rem 2.2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }
    .hero-badge {
        display: inline-block;
        background: var(--navy-deep);
        border: 1.5px solid var(--peach);
        color: var(--peach);
        padding: 5px 16px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-bottom: 1rem;
        letter-spacing: 0.03em;
    }
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.4rem;
        line-height: 1.1;
    }
    .hero-sub {
        color: var(--sage);
        font-size: 1.1rem;
        font-weight: 500;
        max-width: 680px;
    }

    /* Buttons: navy solid inside the blue-light sidebar for contrast */
    .stButton > button {
        background: var(--navy-deep);
        color: var(--peach);
        border: none;
        border-radius: 10px;
        font-weight: 700;
        padding: 0.55rem 1.1rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        background: #001a5c;
        transform: translateY(-1px);
        color: var(--peach);
    }

    /* Text input inside sidebar: white fill so it pops against blue-light */
    .stTextInput > div > div > input {
        background-color: #ffffff;
        color: var(--navy-deep);
        border: 1.5px solid var(--navy-deep);
        border-radius: 8px;
        font-weight: 500;
    }

    /* Info banner: explicit peach card */
    div[data-testid="stAlert"] {
        background: var(--peach) !important;
        border: none;
        border-radius: 12px;
        padding: 1rem;
    }
    div[data-testid="stAlert"] p {
        color: var(--navy-deep) !important;
        font-weight: 600;
    }

    /* Chat bubbles: sage cards with navy text, sitting on the navy page */
    div[data-testid="stChatMessage"] {
        background-color: var(--sage);
        border: none;
        border-radius: 14px;
        padding: 10px 14px;
        box-shadow: 0 3px 14px rgba(0,0,0,0.25);
    }
    div[data-testid="stChatMessage"] p {
        color: var(--navy-deep);
    }

    /* Subheader on the navy page */
    h3 {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--peach);
    }

    /* Expander: blue-mid card */
    div[data-testid="stExpander"] {
        background-color: var(--blue-mid);
        border: none;
        border-radius: 12px;
    }
    div[data-testid="stExpander"] summary {
        color: white;
        font-weight: 700;
    }

    /* Code */
    code {
        color: var(--peach);
        font-weight: 600;
    }
    div[data-testid="stCodeBlock"] {
        border-left: 4px solid var(--peach);
        border-radius: 6px;
    }

    hr {
        border-color: var(--sage);
    }
</style>
""", unsafe_allow_html=True)

# --- Hero card ---
st.markdown("""
<div class="hero-card">
    <div class="hero-badge">⚡ Runs 100% locally · Zero API cost</div>
    <div class="hero-title">🧠 RepoMind</div>
    <div class="hero-sub">
        Code-aware RAG over any GitHub repo. Ask real questions, get grounded answers
        with exact file:line citations — not hallucinated summaries.
    </div>
</div>
""", unsafe_allow_html=True)

# session_state persists data across Streamlit's re-runs
if "collection" not in st.session_state:
    st.session_state.collection = None
if "repo_name" not in st.session_state:
    st.session_state.repo_name = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Sidebar: repo indexing ---
with st.sidebar:
    st.header("⚙️ Index a repo")
    github_url = st.text_input("GitHub URL", placeholder="https://github.com/psf/requests")

    if st.button("🚀 Index repo", type="primary"):
        if not github_url:
            st.error("Paste a GitHub URL first.")
        else:
            with st.spinner("Cloning repo..."):
                repo_root = clone_repo(github_url)
            with st.spinner("Collecting Python files..."):
                files = collect_python_files(repo_root)
            with st.spinner(f"Parsing {len(files)} files into chunks..."):
                chunks = chunk_repo(files)
            with st.spinner(f"Embedding {len(chunks)} chunks..."):
                collection = build_collection(chunks)

            st.session_state.collection = collection
            st.session_state.repo_name = github_url
            st.session_state.chat_history = []
            st.success(f"Indexed {len(chunks)} chunks from {len(files)} files!")

# --- Main area: chat interface ---
if st.session_state.collection is None:
    st.info("👈 Paste a GitHub repo URL in the sidebar and click 'Index repo' to get started.")
else:
    st.subheader(f"💬 Ask questions about: {st.session_state.repo_name}")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Ask a question about this repo...")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking... (local model, may take a bit)"):
                result = answer_question(st.session_state.collection, question)

            st.markdown(result["answer"])

            with st.expander("📄 Sources used"):
                for s in result["sources"]:
                    st.markdown(f"**{s['rel_path']}:{s['start_line']}-{s['end_line']}** — `{s['name']}` ({s['kind']})")
                    st.code(s["code"], language="python")

        st.session_state.chat_history.append({"role": "assistant", "content": result["answer"]})