🧠 RepoMind — Code-Aware RAG over any GitHub Repo

Ask questions about any GitHub repo and get answers grounded in the actual code — with exact file:line citations, not hallucinated summaries.

Runs 100% locally via Ollama — no API key, no cost, no data leaving your machine.

What makes this different from a typical "chat with your docs" RAG bot

Most RAG demos chunk text by raw character count, which for code means broken, meaningless slices — half a function here, a dangling except block there.

RepoMind instead parses every file with Python's ast module and chunks by function, method, and class boundaries, so every retrieved piece of context is a complete, meaningful unit of code — with exact line numbers preserved for citation.

How it works


Ingest — clone any public GitHub repo, filter to relevant Python source files
Chunk — parse each file's AST, split into function/class/method-level chunks
Embed — TF-IDF vectorization (fully local, no model download, works great for code since identifier/keyword overlap is highly informative for search)
Retrieve — find the most relevant chunks for a given question
Answer — a local LLM (via Ollama) answers strictly from retrieved context, citing file:line for every claim
UI — Streamlit chat interface with expandable source code for every answer


Demo

Ask: "How does session authentication get applied to a request?" on psf/requests and get an answer grounded in the actual rebuild_auth implementation, with the exact file and line range cited.

Setup

bash git clone https://github.com/YOUR_USERNAME/repomind.git
cd repomind
python -m venv venv
venv\Scripts\activate   # or source venv/bin/activate on Mac/Linux
pip install -r requirements.txt

Install Ollama, then pull the model:

bashollama pull qwen2.5:3b

Run the app:

bashstreamlit run app.py

Paste any public GitHub repo URL, click Index repo, and start asking questions.

Stack


Parsing: Python ast
Vector store: ChromaDB (in-memory)
Embeddings: scikit-learn TF-IDF
LLM: Ollama (qwen2.5:3b), fully local
UI: Streamlit
