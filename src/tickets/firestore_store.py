from datetime import datetime, timezone
from google.cloud import firestore


db = firestore.Client(
    project="gen-lang-client-0399579856",
    database="default",
)

COLLECTION_NAME = "ticket_drafts"


def save_ticket_draft(draft: dict) -> dict:
    draft_id = draft["draft_id"]

    draft["updated_at"] = datetime.now(timezone.utc).isoformat()

    db.collection(COLLECTION_NAME).document(draft_id).set(draft)

    return draft


def load_ticket_drafts() -> list[dict]:
    docs = (
        db.collection(COLLECTION_NAME)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .stream()
    )

    return [
        doc.to_dict()
        for doc in docs
    ]


def get_ticket_draft(draft_id: str) -> dict | None:
    doc = (
        db.collection(COLLECTION_NAME)
        .document(draft_id)
        .get()
    )

    if not doc.exists:
        return None

    return doc.to_dict()