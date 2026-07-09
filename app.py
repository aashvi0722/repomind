import streamlit as st

from ingest import clone_repo, collect_python_files
from chunker import chunk_repo
from embed_store import build_collection
from qa import answer_question

st.set_page_config(page_title="RepoMind", layout="wide")
st.title("🧠 RepoMind — Code-Aware RAG over any GitHub Repo")
st.caption("Runs fully locally via Ollama — no API key, no cost.")

# session_state persists data across Streamlit's re-runs
if "collection" not in st.session_state:
    st.session_state.collection = None
if "repo_name" not in st.session_state:
    st.session_state.repo_name = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Sidebar: repo indexing ---
with st.sidebar:
    st.header("1. Index a repo")
    github_url = st.text_input("GitHub URL", placeholder="https://github.com/psf/requests")

    if st.button("Index repo", type="primary"):
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
    st.subheader(f"Ask questions about: {st.session_state.repo_name}")

    # replay chat history
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