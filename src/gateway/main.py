import os
import time
import httpx
from pydantic import BaseModel

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, Response


AGENT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")

app = FastAPI(
    title="Enterprise AI API Gateway",
    version="1.0.0",
)


async def proxy_request(
    request: Request,
    path: str,
):
    start = time.time()

    target_url = f"{AGENT_API_URL}{path}"

    body = await request.body()

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in ["host", "content-length"]
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
            params=request.query_params,
        )

    latency_ms = int((time.time() - start) * 1000)

    print(
        {
            "event": "gateway_proxy",
            "method": request.method,
            "path": path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        },
        flush=True,
    )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type"),
    )

class CreateJobRequest(BaseModel):
    query: str
    session_id: str | None = None

class FeedbackRequest(BaseModel):
    rating: int
    comment: str | None = None

@app.get("/health")
async def health(request: Request):
    return await proxy_request(request, "/health")


@app.get("/ready")
async def ready(request: Request):
    return await proxy_request(request, "/ready")


@app.post("/support-jobs")
async def create_job(body: CreateJobRequest, request: Request):
    return await proxy_request(request, "/support-jobs")


@app.get("/support-jobs/{job_id}")
async def get_job(job_id: str, request: Request):
    return await proxy_request(request, f"/support-jobs/{job_id}")


@app.get("/support-jobs/{job_id}/result")
async def get_job_result(job_id: str, request: Request):
    return await proxy_request(request, f"/support-jobs/{job_id}/result")


@app.post("/support-jobs/{job_id}/cancel")
async def cancel_job(job_id: str, request: Request):
    return await proxy_request(request, f"/support-jobs/{job_id}/cancel")


@app.post("/support-jobs/{job_id}/feedback")
async def feedback(job_id: str, body: FeedbackRequest, request: Request):
    return await proxy_request(request, f"/support-jobs/{job_id}/feedback")


@app.get("/support-jobs/{job_id}/events")
async def job_events(job_id: str, request: Request):
    target_url = f"{AGENT_API_URL}/support-jobs/{job_id}/events"

    async def event_stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "GET",
                target_url,
                params=request.query_params,
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )