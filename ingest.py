import os
import tempfile
import git

def clone_repo(github_url: str) -> str:
    dest_dir = tempfile.mkdtemp(prefix="repomind_")
    git.Repo.clone_from(github_url, dest_dir, depth=1)
    return dest_dir

SKIP_DIRS = {".git", "__pycache__", "node_modules", "venv", ".venv", "env", "build", "dist"}

def collect_python_files(repo_root: str) -> list[dict]:
    results = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, repo_root)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except OSError:
                continue
            results.append({"path": full_path, "rel_path": rel_path, "content": content})
    return results

if __name__ == "__main__":
    path = clone_repo("https://github.com/psf/requests")
    print("Cloned to:", path)
    files = collect_python_files(path)
    print(f"Found {len(files)} Python files")
    for f in files[:5]:
        print(" -", f["rel_path"])