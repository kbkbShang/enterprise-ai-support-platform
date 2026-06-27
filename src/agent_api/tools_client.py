import os
import requests
from dotenv import load_dotenv


load_dotenv()

TOOL_SERVER_URL = os.getenv("TOOL_SERVER_URL", "http://localhost:7001")


def call_search_kb(query: str, top_k: int = 3) -> dict:
    print(f"[call_search_kb] TOOL_SERVER_URL={TOOL_SERVER_URL}", flush=True)
    print(f"[call_search_kb] query={query}, top_k={top_k}", flush=True)

    response = requests.post(
        f"{TOOL_SERVER_URL}/tools/search_kb",
        json={
            "query": query,
            "top_k": top_k,
        },
        timeout=30,
    )

    print(f"[call_search_kb] status={response.status_code}, body={response.text[:500]}", flush=True)

    response.raise_for_status()
    return response.json()


def call_get_kb_doc(doc_id: str) -> dict:
    response = requests.post(
        f"{TOOL_SERVER_URL}/tools/get_kb_doc",
        json={
            "doc_id": doc_id,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def call_search_tickets(
    query: str,
    status: str | None = None,
    tags: list[str] | None = None,
    top_k: int = 3,
) -> dict:
    response = requests.post(
        f"{TOOL_SERVER_URL}/tools/search_tickets",
        json={
            "query": query,
            "status": status,
            "tags": tags,
            "top_k": top_k,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def call_create_ticket_draft(
    title: str,
    description: str,
    priority: str = "medium",
    tags: list[str] | None = None,
) -> dict:
    response = requests.post(
        f"{TOOL_SERVER_URL}/tools/create_ticket_draft",
        json={
            "title": title,
            "description": description,
            "priority": priority,
            "tags": tags or [],
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    result = call_search_kb("VPN authentication failed", top_k=3)
    print(result)