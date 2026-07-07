import time
import os
import socket

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.scheduler import ThreadScheduler
from concurrent.futures import ThreadPoolExecutor

from src.agent_api.gemini_agent_v3 import run_gemini_agent
from src.jobs.job_store import (
    get_support_job,
    mark_job_running,
    append_job_progress,
    save_job_result,
    fail_job,
    should_cancel,
    increment_attempt,
)
from src.jobs.dlq_client import publish_to_dlq

import time

from fastapi import FastAPI
import threading

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "worker": "running"}

@app.on_event("startup")
def start_worker():
    thread = threading.Thread(target=main, daemon=True)
    thread.start()
    
#print("Worker module loaded")
PROJECT_ID = "gen-lang-client-0399579856"
SUBSCRIPTION_ID = "support-jobs-sub"

MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

WORKER_ID = os.getenv("WORKER_ID", socket.gethostname())

subscriber = pubsub_v1.SubscriberClient()

subscription_path = subscriber.subscription_path(
    PROJECT_ID,
    SUBSCRIPTION_ID,
)

def stop_if_cancelled(job_id: str) -> bool:
    if should_cancel(job_id):
        append_job_progress(
            job_id,
            "Worker detected cancellation. Stopping execution.",
        )
        print(f"Job cancelled: {job_id}")
        return True

    return False

def run_agent_with_retry(job_id: str, query: str, max_attempts: int = 3) -> dict:
    last_error = None

    for attempt in range(1, max_attempts + 1):
        if stop_if_cancelled(job_id):
            raise RuntimeError("Job was cancelled.")

        increment_attempt(job_id)

        append_job_progress(
            job_id,
            f"Agent attempt {attempt}/{max_attempts} started.",
        )

        try:

            #if "force retry" in query.lower():
                #raise RuntimeError("Simulated transient failure for retry testing.")
    
            result = run_gemini_agent(query)

            append_job_progress(
                job_id,
                f"Agent attempt {attempt}/{max_attempts} succeeded.",
            )

            return result

        except Exception as e:
            last_error = str(e)

            append_job_progress(
                job_id,
                f"Agent attempt {attempt}/{max_attempts} failed: {last_error}",
            )

            if attempt < max_attempts:
                sleep_seconds = 2 ** attempt

                append_job_progress(
                    job_id,
                    f"Retrying after {sleep_seconds} seconds.",
                )

                time.sleep(sleep_seconds)

    raise RuntimeError(last_error or "Agent failed after retries.")

def process_job(job_id: str):
    import threading

    print(
        job_id,
        threading.current_thread().name
    )
    
    job = get_support_job(job_id)

    if not job:
        print(f"Job not found: {job_id}")
        return

    if stop_if_cancelled(job_id):
        return

    job = mark_job_running(job_id, worker_id=WORKER_ID)

    if not job or not job.get("claimed"):
        print(f"Skipping job {job_id}; current status is {job.get('status') if job else 'missing'}")
        return

    append_job_progress(
        job_id,
        "Worker started processing the job.",
    )

    if stop_if_cancelled(job_id):
        return

    try:
        query = job["query"]

        append_job_progress(
            job_id,
            "Running agent workflow.",
        )

        if stop_if_cancelled(job_id):
            return

        max_attempts = job.get("max_attempts", 3)

        result = run_agent_with_retry(
            job_id=job_id,
            query=query,
            max_attempts=max_attempts,
        )

        if stop_if_cancelled(job_id):
            return

        append_job_progress(
            job_id,
            "Agent workflow completed.",
        )

        save_job_result(
            job_id,
            result,
        )

        print(f"Job completed: {job_id}")

    except Exception as e:
        if stop_if_cancelled(job_id):
            return

        dlq_message_id = publish_to_dlq(
            job_id=job_id,
            error=str(e),
        )

        fail_job(job_id, str(e), dlq_message_id=dlq_message_id)

        append_job_progress(
            job_id,
            f"Job sent to DLQ with message_id={dlq_message_id}.",
        )

        print(f"Job failed and sent to DLQ: {job_id} - {str(e)}")


def callback(pubsub_message):
    job_id = pubsub_message.data.decode("utf-8")

    print(f"Received job: {job_id}")

    try:
        process_job(job_id)

        pubsub_message.ack()

        print(f"Acked job: {job_id}")

    except Exception as e:
        print(f"Worker error for job {job_id}: {str(e)}")

        pubsub_message.nack()

def main():
    #print("Entering main()")
    #print(f"Listening for messages on {subscription_path}")
    print(f"Listening for messages on {subscription_path}")

    flow_control = pubsub_v1.types.FlowControl(
        max_messages=4,
        max_lease_duration=600,
    )

    scheduler = ThreadScheduler(ThreadPoolExecutor(max_workers=4))

    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=callback,
        flow_control=flow_control,
        scheduler=scheduler,
    )

    try:
        streaming_pull_future.result()

    except KeyboardInterrupt:
        print("Stopping worker...")
        streaming_pull_future.cancel()
        streaming_pull_future.result()   
        print("Worker stopped.")


if __name__ == "__main__":
    main()