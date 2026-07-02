from fastapi import APIRouter

from src.metrics.metrics_store import get_job_metrics


router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
)


@router.get("")
def metrics():
    return get_job_metrics()