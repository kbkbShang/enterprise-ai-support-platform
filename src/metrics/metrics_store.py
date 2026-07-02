from google.cloud import firestore


db = firestore.Client(
    project="gen-lang-client-0399579856",
    database="default",
)

JOBS_COLLECTION = "support_jobs"


def safe_number(value):
    if isinstance(value, (int, float)):
        return value
    return None


def average(values: list[float]) -> float:
    if not values:
        return 0.0

    return round(sum(values) / len(values), 2)


def get_job_metrics() -> dict:
    docs = db.collection(JOBS_COLLECTION).stream()

    total = 0
    queued = 0
    running = 0
    completed = 0
    failed = 0
    cancelled = 0

    queue_latencies = []
    processing_latencies = []
    llm_latencies = []

    ticket_created_count = 0
    total_citations = 0
    total_tool_calls = 0

    for doc in docs:
        job = doc.to_dict()
        total += 1

        status = job.get("status")

        if status == "queued":
            queued += 1
        elif status == "running":
            running += 1
        elif status == "completed":
            completed += 1
        elif status == "failed":
            failed += 1
        elif status == "cancelled":
            cancelled += 1

        queue_latency = safe_number(job.get("queue_latency_ms"))
        if queue_latency is not None:
            queue_latencies.append(queue_latency)

        processing_latency = safe_number(job.get("processing_latency_ms"))
        if processing_latency is not None:
            processing_latencies.append(processing_latency)

        result = job.get("result") or {}
        metadata = result.get("metadata") or {}
        ticket_draft = result.get("ticket_draft") or {}

        llm_latency = safe_number(metadata.get("latency_ms"))
        if llm_latency is not None:
            llm_latencies.append(llm_latency)

        if ticket_draft.get("created"):
            ticket_created_count += 1

        total_citations += metadata.get("citation_count", 0) or 0
        total_tool_calls += metadata.get("tool_call_count", 0) or 0

    success_rate = round((completed / total) * 100, 2) if total else 0.0

    avg_citations_per_completed_job = (
        round(total_citations / completed, 2)
        if completed
        else 0.0
    )

    return {
        "jobs": {
            "total": total,
            "queued": queued,
            "running": running,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "success_rate": success_rate,
        },
        "performance": {
            "avg_queue_latency_ms": average(queue_latencies),
            "avg_processing_latency_ms": average(processing_latencies),
            "avg_llm_latency_ms": average(llm_latencies),
        },
        "agent": {
            "ticket_created_count": ticket_created_count,
            "total_citations": total_citations,
            "avg_citations_per_completed_job": avg_citations_per_completed_job,
            "total_tool_calls": total_tool_calls,
        },
    }