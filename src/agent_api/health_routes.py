import os
import time
import requests

from fastapi import APIRouter
from google.cloud import firestore
from google.cloud import pubsub_v1


router = APIRouter(tags=["health"])

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0399579856")
TOOL_SERVER_URL = os.getenv("TOOL_SERVER_URL")
PUBSUB_TOPIC = os.getenv("PUBSUB_TOPIC", "support-jobs")
PUBSUB_SUBSCRIPTION = os.getenv("PUBSUB_SUBSCRIPTION", "support-jobs-sub")

def check_firestore() -> dict:
    start = time.time()

    try:
        db = firestore.Client(
            project=PROJECT_ID,
            database="default",
        )

        docs = db.collection("support_jobs").limit(1).stream()
        next(docs, None)

        return {
            "status": "ok",
            "latency_ms": int((time.time() - start) * 1000),
        }

    except Exception as e:
        return {
            "status": "error",
            "latency_ms": int((time.time() - start) * 1000),
            "error": str(e),
        }


def check_tool_server() -> dict:
    start = time.time()

    if not TOOL_SERVER_URL:
        return {
            "status": "error",
            "latency_ms": 0,
            "error": "TOOL_SERVER_URL is not configured",
        }

    try:
        response = requests.get(
            f"{TOOL_SERVER_URL}/health",
            timeout=5,
        )

        return {
            "status": "ok" if response.status_code == 200 else "error",
            "latency_ms": int((time.time() - start) * 1000),
            "status_code": response.status_code,
        }

    except Exception as e:
        return {
            "status": "error",
            "latency_ms": int((time.time() - start) * 1000),
            "error": str(e),
        }


def check_pubsub() -> dict:
    start = time.time()

    try:
        publisher = pubsub_v1.PublisherClient()
        subscriber = pubsub_v1.SubscriberClient()

        topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
        subscription_path = subscriber.subscription_path(
            PROJECT_ID,
            PUBSUB_SUBSCRIPTION,
        )

        publisher.get_topic(request={"topic": topic_path})
        subscriber.get_subscription(
            request={"subscription": subscription_path}
        )

        return {
            "status": "ok",
            "latency_ms": int((time.time() - start) * 1000),
            "topic": PUBSUB_TOPIC,
            "subscription": PUBSUB_SUBSCRIPTION,
        }

    except Exception as e:
        return {
            "status": "error",
            "latency_ms": int((time.time() - start) * 1000),
            "error": str(e),
            "topic": PUBSUB_TOPIC,
            "subscription": PUBSUB_SUBSCRIPTION,
        }


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "agent_api",
    }


@router.get("/ready")
def ready():
    checks = {
        "firestore": check_firestore(),
        "tool_server": check_tool_server(),
        "pubsub": check_pubsub(),
    }

    ready_status = all(
        check.get("status") == "ok"
        for check in checks.values()
    )

    return {
        "ready": ready_status,
        "service": "agent_api",
        "checks": checks,
    }