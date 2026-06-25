from google.cloud import pubsub_v1

PROJECT_ID = "gen-lang-client-0399579856"
DLQ_TOPIC_ID = "support-jobs-dlq"

publisher = pubsub_v1.PublisherClient()

dlq_topic_path = publisher.topic_path(
    PROJECT_ID,
    DLQ_TOPIC_ID,
)

def publish_to_dlq(job_id: str, error: str) -> str:
    message_data = job_id.encode("utf-8")

    future = publisher.publish(
        dlq_topic_path,
        message_data,
        error=error,
    )

    return future.result()