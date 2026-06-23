from src.rag.loader import load_kb_documents

def chunk_document(doc: dict) -> list[dict]:
    """
    Split one markdown document into chunks by H2 headings.
    Each chunk keeps doc_id, chunk_id, heading, and text.
    """
    lines = doc["content"].splitlines()

    chunks = []
    current_heading = doc["title"]
    current_lines = []

    chunk_index = 1

    for line in lines:
        if line.startswith("## "):
            if current_lines:
                chunks.append(
                    {
                        "doc_id": doc["doc_id"],
                        "chunk_id": f"{doc['doc_id']}#{chunk_index:03d}",
                        "title": doc["title"],
                        "heading": current_heading,
                        "text": "\n".join(current_lines).strip(),
                        "source_path": doc["source_path"],
                    }
                )
                chunk_index += 1

            current_heading = line.replace("## ", "").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        chunks.append(
            {
                "doc_id": doc["doc_id"],
                "chunk_id": f"{doc['doc_id']}#{chunk_index:03d}",
                "title": doc["title"],
                "heading": current_heading,
                "text": "\n".join(current_lines).strip(),
                "source_path": doc["source_path"],
            }
        )

    return chunks


def chunk_kb_documents(docs: list[dict]) -> list[dict]:
    """
    Chunk all KB documents.
    """
    all_chunks = []

    for doc in docs:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)

    return all_chunks


if __name__ == "__main__":
    docs = load_kb_documents()
    chunks = chunk_kb_documents(docs)

    print(f"Loaded {len(docs)} documents")
    print(f"Created {len(chunks)} chunks")

    for chunk in chunks[:5]:
        print("=" * 60)
        print(chunk["chunk_id"])
        print(chunk["heading"])
        print(chunk["text"][:300])