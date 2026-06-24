from typing import Literal
from pydantic import BaseModel, Field


JobStatus = Literal[
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
]


class CreateSupportJobRequest(BaseModel):
    query: str = Field(..., min_length=1)
    session_id: str | None = None


class SupportJobResponse(BaseModel):
    job_id: str
    status: JobStatus


class SubmitFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None