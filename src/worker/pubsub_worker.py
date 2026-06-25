#print("TOP OF WORKER FILE", flush=True)
import time

from google.cloud import pubsub_v1

from src.agent_api.gemini_agent_v3 import run_gemini_agent
from src.jobs.job_store import (
    get_support_job,
    update_support_job,
    append_job_progress,
    save_job_result,
    fail_job,
)

#print("Worker module loaded")
PROJECT_ID = "gen-lang-client-0399579856"
SUBSCRIPTION_ID = "support-jobs-sub"


subscriber = pubsub_v1.SubscriberClient()

subscription_path = subscriber.subscription_path(
    PROJECT_ID,
    SUBSCRIPTION_ID,
)


def process_job(job_id: str):
    job = get_support_job(job_id)

    if not job:
        print(f"Job not found: {job_id}")
        return

    if job.get("status") == "cancelled":
        print(f"Job already cancelled: {job_id}")
        return

    update_support_job(
        job_id,
        {
            "status": "running",
        },
    )

    append_job_progress(
        job_id,
        "Worker started processing the job.",
    )

    try:
        query = job["query"]

        append_job_progress(
            job_id,
            "Running agent workflow.",
        )

        result = run_gemini_agent(query)

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
        fail_job(
            job_id,
            str(e),
        )

        print(f"Job failed: {job_id} - {str(e)}")


def callback(message):
    job_id = message.data.decode("utf-8")

    print(f"Received job: {job_id}")

    try:
        process_job(job_id)

        message.ack()

        print(f"Acked job: {job_id}")

    except Exception as e:
        print(f"Worker error for job {job_id}: {str(e)}")

        message.nack()


def main():
    #print("Entering main()")
    #print(f"Listening for messages on {subscription_path}")
    print(f"Listening for messages on {subscription_path}")

    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=callback,
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