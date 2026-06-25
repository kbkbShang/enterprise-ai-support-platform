from fastapi import APIRouter, HTTPException

from src.jobs.schemas import (
    CreateSupportJobRequest,
    SubmitFeedbackRequest,
)

from src.jobs.job_store import (
    create_support_job,
    get_support_job,
    cancel_job,
    save_feedback,
)

from src.jobs.pubsub_client import publish_job


router = APIRouter(
    prefix="/support-jobs",
    tags=["support-jobs"],
)


@router.post("")
def create_job(request: CreateSupportJobRequest):
    job = create_support_job(
        query=request.query,
        session_id=request.session_id,
    )
    message_id = publish_job(job["job_id"])

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "created_at": job["created_at"],
        "message_id": message_id,
    }


@router.get("/{job_id}")
def get_job_status(job_id: str):
    job = get_support_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job.get("progress", []),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
    }


@router.get("/{job_id}/result")
def get_job_result(job_id: str):
    job = get_support_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job["status"] == "completed":
        return {
            "job_id": job_id,
            "status": job["status"],
            "result": job.get("result"),
        }

    if job["status"] == "cancelled":
        return {
            "job_id": job_id,
            "status": "cancelled",
            "result": None,
            "message": "Job was cancelled before completion.",
        }

    if job["status"] == "failed":
        return {
            "job_id": job_id,
            "status": "failed",
            "result": None,
            "error": job.get("error"),
        }

    return {
        "job_id": job_id,
        "status": job["status"],
        "result": None,
        "message": "Job is still in progress.",
    }


@router.post("/{job_id}/cancel")
def cancel_support_job(job_id: str):
    job = cancel_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return {
        "job_id": job_id,
        "status": job["status"],
        "cancel_requested": job.get("cancel_requested", False),
    }


@router.post("/{job_id}/feedback")
def submit_feedback(
    job_id: str,
    request: SubmitFeedbackRequest,
):
    job = get_support_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    feedback = save_feedback(
        job_id=job_id,
        rating=request.rating,
        comment=request.comment,
    )

    return {
        "saved": True,
        "feedback": feedback,
    }