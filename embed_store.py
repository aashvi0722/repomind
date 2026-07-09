import chromadb
from chromadb import EmbeddingFunction
from sklearn.feature_extraction.text import TfidfVectorizer


class TfidfEmbeddingFunction(EmbeddingFunction):
    def __init__(self, max_features: int = 4000):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            token_pattern=r"[A-Za-z_][A-Za-z0-9_]+",
            lowercase=True,
            sublinear_tf=True,
        )
        self._fitted = False

    def fit(self, corpus: list[str]):
        self.vectorizer.fit(corpus)
        self._fitted = True

    def __call__(self, input: list[str]) -> list[list[float]]:
        if not self._fitted:
            self.vectorizer.fit(input)
            self._fitted = True
        matrix = self.vectorizer.transform(input)
        return matrix.toarray().tolist()


def build_collection(chunks: list[dict], collection_name: str = "repo_chunks"):
    documents = []
    for c in chunks:
        doc_text = f"{c['name']} ({c['kind']}) in {c['rel_path']}\n{c['code']}"
        documents.append(doc_text)

    embedding_fn = TfidfEmbeddingFunction()
    embedding_fn.fit(documents)

    client = chromadb.EphemeralClient()
    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
    )

    ids = [c["id"] for c in chunks]
    metadatas = []
    for c in chunks:
        metadatas.append({
            "rel_path": c["rel_path"],
            "name": c["name"],
            "kind": c["kind"],
            "start_line": c["start_line"],
            "end_line": c["end_line"],
            "code": c["code"],
        })

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return collection


def query_collection(collection, query: str, n_results: int = 6):
    results = collection.query(query_texts=[query], n_results=n_results)

    hits = []
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i]
        hits.append({
            "id": results["ids"][0][i],
            "rel_path": meta["rel_path"],
            "name": meta["name"],
            "kind": meta["kind"],
            "start_line": meta["start_line"],
            "end_line": meta["end_line"],
            "code": meta["code"],
            "distance": results["distances"][0][i],
        })
    return hits


if __name__ == "__main__":
    from ingest import clone_repo, collect_python_files
    from chunker import chunk_repo

    path = clone_repo("https://github.com/psf/requests")
    files = collect_python_files(path)
    chunks = chunk_repo(files)

    print(f"Embedding {len(chunks)} chunks...")
    collection = build_collection(chunks)
    print("Done. Collection built with", collection.count(), "items.")

    hits = query_collection(collection, "how does session authentication work", n_results=5)
    for h in hits:
        print(f" - {h['rel_path']}:{h['start_line']}-{h['end_line']}  {h['name']} ({h['kind']})  distance={h['distance']:.3f}")