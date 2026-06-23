from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from src.rag.loader import load_kb_documents
from src.rag.chunker import chunk_kb_documents


CHROMA_DIR = Path("data/chroma")
COLLECTION_NAME = "kb_chunks"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def build_index():
    """
    Build a Chroma vector index from KB markdown documents.
    """
    print("Loading KB documents...")
    docs = load_kb_documents()

    print(f"Loaded {len(docs)} documents")

    print("Chunking documents...")
    chunks = chunk_kb_documents(docs)

    print(f"Created {len(chunks)} chunks")

    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    texts = [chunk["text"] for chunk in chunks]
    ids = [chunk["chunk_id"] for chunk in chunks]

    metadatas = [
        {
            "doc_id": chunk["doc_id"],
            "chunk_id": chunk["chunk_id"],
            "title": chunk["title"],
            "heading": chunk["heading"],
            "source_path": chunk["source_path"],
        }
        for chunk in chunks
    ]

    print("Generating embeddings...")
    embeddings = model.encode(texts, convert_to_numpy=True).tolist()

    print("Creating Chroma collection...")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Delete old collection if it exists, so rebuild is clean
    existing_collections = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing_collections:
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(name=COLLECTION_NAME)

    print("Adding chunks to Chroma...")
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print("Index build complete.")
    print(f"Saved to: {CHROMA_DIR}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Total chunks indexed: {collection.count()}")


if __name__ == "__main__":
    build_index()