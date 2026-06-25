from google.cloud import pubsub_v1

PROJECT_ID = "gen-lang-client-0399579856"
TOPIC_ID = "support-jobs"

publisher = pubsub_v1.PublisherClient()

topic_path = publisher.topic_path(
    PROJECT_ID,
    TOPIC_ID,
)


def publish_job(job_id: str):
    future = publisher.publish(
        topic_path,
        job_id.encode("utf-8"),
    )

    message_id = future.result()

    return message_id