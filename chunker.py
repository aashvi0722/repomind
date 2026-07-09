import ast

MAX_CHUNK_CHARS = 4000

def chunk_file(rel_path: str, content: str) -> list[dict]:
    chunks = []
    lines = content.splitlines()

    try:
        tree = ast.parse(content, filename=rel_path)
    except SyntaxError:
        return chunks

    def extract(node, class_name=None):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = child.lineno
                end = child.end_lineno
                name = f"{class_name}.{child.name}" if class_name else child.name
                code = "\n".join(lines[start - 1:end])
                chunks.append({
                    "name": name,
                    "start_line": start,
                    "end_line": end,
                    "code": code,
                    "rel_path": rel_path,
                    "kind": "method" if class_name else "function",
                })
            elif isinstance(child, ast.ClassDef):
                start = child.lineno
                end = child.end_lineno
                code = "\n".join(lines[start - 1:end])
                chunks.append({
                    "name": child.name,
                    "start_line": start,
                    "end_line": end,
                    "code": code,
                    "rel_path": rel_path,
                    "kind": "class",
                })
                extract(child, class_name=child.name)

    extract(tree)
    return chunks


def chunk_repo(files: list[dict]) -> list[dict]:
    all_chunks = []
    seen_ids = {}

    for f in files:
        file_chunks = chunk_file(f["rel_path"], f["content"])
        for c in file_chunks:
            base_id = f"{c['rel_path']}::{c['name']}"
            if base_id in seen_ids:
                seen_ids[base_id] += 1
                c["id"] = f"{base_id}#{c['start_line']}"
            else:
                seen_ids[base_id] = 1
                c["id"] = base_id
            all_chunks.append(c)

    return all_chunks


if __name__ == "__main__":
    from ingest import clone_repo, collect_python_files

    path = clone_repo("https://github.com/psf/requests")
    files = collect_python_files(path)

    chunks = chunk_repo(files)
    print(f"Total chunks: {len(chunks)}")
    for c in chunks[:10]:
        print(f"[{c['kind']}] {c['id']}  lines {c['start_line']}-{c['end_line']}")