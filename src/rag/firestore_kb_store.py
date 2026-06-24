from datetime import datetime, timezone
from google.cloud import firestore


db = firestore.Client(
    project="gen-lang-client-0399579856",
    database="default",
)

DOCS_COLLECTION = "kb_docs"
CHUNKS_COLLECTION = "kb_chunks"


def upsert_kb_doc(
    doc_id: str,
    title: str,
    text: str,
    source_path: str,
) -> dict:
    record = {
        "doc_id": doc_id,
        "title": title,
        "text": text,
        "source_path": source_path,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    db.collection(DOCS_COLLECTION).document(doc_id).set(record)

    return record


def upsert_kb_chunk(
    chunk_id: str,
    doc_id: str,
    heading: str,
    text: str,
    source_path: str,
) -> dict:
    record = {
        "chunk_id": chunk_id,
        "doc_id": doc_id,
        "heading": heading,
        "text": text,
        "source_path": source_path,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    db.collection(CHUNKS_COLLECTION).document(chunk_id).set(record)

    return record


def get_kb_chunk(chunk_id: str) -> dict | None:
    doc = db.collection(CHUNKS_COLLECTION).document(chunk_id).get()

    if not doc.exists:
        return None

    return doc.to_dict()


def get_kb_doc(doc_id: str) -> dict | None:
    doc = db.collection(DOCS_COLLECTION).document(doc_id).get()

    if not doc.exists:
        return None

    return doc.to_dict()