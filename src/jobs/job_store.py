from datetime import datetime, timezone
import uuid

from google.cloud import firestore


db = firestore.Client(
    project="gen-lang-client-0399579856",
    database="default",
)

JOBS_COLLECTION = "support_jobs"
FEEDBACK_COLLECTION = "support_feedback"

TERMINAL_STATUSES = {"completed", "failed", "cancelled"}

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_support_job(
    query: str,
    session_id: str | None = None,
) -> dict:
    job_id = f"job_{uuid.uuid4().hex[:12]}"

    job = {
        "job_id": job_id,
        "query": query,
        "session_id": session_id,
        "status": "queued",
        "progress": ["Job created."],
        "result": None,
        "error": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "started_at": None,
        "finished_at": None,
    }

    db.collection(JOBS_COLLECTION).document(job_id).set(job)

    return job


def get_support_job(job_id: str) -> dict | None:
    doc = db.collection(JOBS_COLLECTION).document(job_id).get()

    if not doc.exists:
        return None

    return doc.to_dict()


def update_support_job(
    job_id: str,
    updates: dict,
) -> dict | None:
    updates["updated_at"] = now_iso()

    doc_ref = db.collection(JOBS_COLLECTION).document(job_id)
    doc_ref.update(updates)

    return get_support_job(job_id)


def append_job_progress(
    job_id: str,
    message: str,
) -> dict | None:
    doc_ref = db.collection(JOBS_COLLECTION).document(job_id)

    doc_ref.update(
        {
            "progress": firestore.ArrayUnion([message]),
            "updated_at": now_iso(),
        }
    )

    return get_support_job(job_id)

def mark_job_running(job_id: str) -> dict | None:
    job = get_support_job(job_id)

    if not job:
        return None

    if job["status"] in TERMINAL_STATUSES:
        return job

    return update_support_job(
        job_id,
        {
            "status": "running",
            "started_at": now_iso(),
        },
    )

def save_job_result(
    job_id: str,
    result: dict,
) -> dict | None:
    job = get_support_job(job_id)

    if not job:
        return None

    if job["status"] == "cancelled":
        return job

    return update_support_job(
        job_id,
        {
            "status": "completed",
            "result": result,
            "error": None,
            "finished_at": now_iso(),
        },
    )


def fail_job(
    job_id: str,
    error: str,
) -> dict | None:
    job = get_support_job(job_id)

    if not job:
        return None

    if job["status"] == "cancelled":
        return job

    return update_support_job(
        job_id,
        {
            "status": "failed",
            "error": error,
            "finished_at": now_iso(),
        },
    )


def cancel_job(job_id: str) -> dict | None:
    job = get_support_job(job_id)

    if not job:
        return None

    if job["status"] in TERMINAL_STATUSES:
        return job

    return update_support_job(
        job_id,
        {
            "status": "cancelled",
            "finished_at": now_iso(),
        },
    )

def should_cancel(job_id: str) -> bool:
    job = get_support_job(job_id)

    if not job:
        return True

    return job.get("status") == "cancelled"

def save_feedback(
    job_id: str,
    rating: int,
    comment: str | None = None,
) -> dict:
    feedback_id = f"feedback_{uuid.uuid4().hex[:12]}"

    feedback = {
        "feedback_id": feedback_id,
        "job_id": job_id,
        "rating": rating,
        "comment": comment,
        "created_at": now_iso(),
    }

    db.collection(FEEDBACK_COLLECTION).document(feedback_id).set(feedback)

    return feedback