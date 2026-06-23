from pathlib import Path

KB_DIR = Path("data/kb")

def load_kb_documents(kb_dir: Path = KB_DIR) -> list[dict]:
    """
    Load all markdown knowledge base documents.

    Returns:
        A list of documents.
        Each document contains:
        - doc_id
        - title
        - content
        - source_path
    """
    documents = []

    for file_path in kb_dir.glob("*.md"):
        content = file_path.read_text(encoding="utf-8")

        doc_id = file_path.stem

        title = extract_title(content, fallback=doc_id)

        documents.append(
            {
                "doc_id": doc_id,
                "title": title,
                "content": content,
                "source_path": str(file_path),
            }
        )

    return documents


def extract_title(content: str, fallback: str) -> str:
    """
    Extract the first markdown H1 title from a document.
    If no title is found, use the file name as fallback.
    """
    for line in content.splitlines():
        if line.startswith("# "):
            return line.replace("# ", "").strip()

    return fallback


if __name__ == "__main__":
    docs = load_kb_documents()

    print(f"Loaded {len(docs)} KB documents")

    for doc in docs:
        print(f"- {doc['doc_id']}: {doc['title']}")