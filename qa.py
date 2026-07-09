import requests

from embed_store import query_collection

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"

SYSTEM_PROMPT = """You are a code assistant answering questions about a specific GitHub repository.
You will be given retrieved code chunks, each labeled with its file path and line range.

Rules:
1. Answer ONLY using the provided code chunks. Do not invent behavior that isn't shown.
2. Every factual claim about how the code works MUST be followed by a citation in the
   form (file_path:start_line-end_line).
3. If the retrieved chunks don't contain enough information to answer, say so plainly.
4. Be concise and technical.
"""


def format_context(hits: list[dict]) -> str:
    blocks = []
    for h in hits:
        blocks.append(
            f"--- {h['rel_path']}:{h['start_line']}-{h['end_line']} "
            f"({h['kind']}: {h['name']}) ---\n{h['code']}"
        )
    return "\n\n".join(blocks)


def answer_question(collection, question: str, n_results: int = 6) -> dict:
    hits = query_collection(collection, question, n_results=n_results)
    context = format_context(hits)

    full_prompt = f"{SYSTEM_PROMPT}\n\nRetrieved code context:\n\n{context}\n\nQuestion: {question}"

    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False,
    })
    response.raise_for_status()
    answer_text = response.json()["response"]

    return {"answer": answer_text, "sources": hits}


if __name__ == "__main__":
    from ingest import clone_repo, collect_python_files
    from chunker import chunk_repo
    from embed_store import build_collection

    path = clone_repo("https://github.com/psf/requests")
    files = collect_python_files(path)
    chunks = chunk_repo(files)
    collection = build_collection(chunks)

    result = answer_question(collection, "How does session authentication get applied to a request?")
    print("ANSWER:\n", result["answer"])
    print("\nSOURCES:")
    for s in result["sources"]:
        print(f" - {s['rel_path']}:{s['start_line']}-{s['end_line']}  {s['name']}")