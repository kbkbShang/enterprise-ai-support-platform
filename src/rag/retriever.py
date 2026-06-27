from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from src.rag.loader import load_kb_documents
from src.rag.firestore_kb_store import get_kb_chunk
from src.rag.firestore_kb_store import get_kb_doc as get_kb_doc_firestore

CHROMA_DIR = Path("data/chroma")
COLLECTION_NAME = "kb_chunks"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


#model = SentenceTransformer(EMBEDDING_MODEL_NAME)
model = None


def get_model():
    global model

    if model is None:
        print("Loading embedding model...")
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    return model


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(name=COLLECTION_NAME)


def search_kb(query: str, top_k: int = 5) -> list[dict]:
    """
    Search KB chunks from Chroma using embedding similarity.
    """
    collection = get_collection()

    # Generate embedding for one query
    #query_embedding = model.encode([query], convert_to_numpy=True).tolist()[0]
    embedding_model = get_model()
    query_embedding = embedding_model.encode([query], convert_to_numpy=True).tolist()[0]

    # Query the collection for similar chunks(cosine similarity search)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    output = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc_text, metadata, distance in zip(documents, metadatas, distances):
        score = 1 / (1 + distance)

        chunk_id = metadata["chunk_id"]

        chunk_record = get_kb_chunk(chunk_id)

        if chunk_record:
            text = chunk_record.get("text", doc_text)
            heading = chunk_record.get(
                "heading",
                metadata.get("heading", "")
            )
        else:
            text = doc_text
            heading = metadata.get("heading", "")

        output.append(
            {
                "doc_id": metadata["doc_id"],
                "chunk_id": chunk_id,
                "score": round(score, 4),
                "heading": heading,
                "text": text,
            }
    )

    return output


def get_kb_doc(doc_id: str) -> dict | None:
    record = get_kb_doc_firestore(doc_id)

    if not record:
        return None

    return {
        "doc_id": record["doc_id"],
        "title": record["title"],
        "content": record["text"],
        "metadata": {
            "source_path": record["source_path"]
        }
    }


if __name__ == "__main__":
    query = "VPN authentication failed"
    results = search_kb(query, top_k=3)

    print(f"Query: {query}")
    print(f"Found {len(results)} results")

    for result in results:
        print("=" * 60)
        print(result["doc_id"], result["chunk_id"], result["score"])
        print(result["heading"])
        print(result["text"][:300])