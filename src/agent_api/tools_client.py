import os
import requests
from dotenv import load_dotenv
import time


load_dotenv()

TOOL_SERVER_URL = os.getenv("TOOL_SERVER_URL", "http://localhost:7001")


def call_search_kb(query: str, top_k: int = 3) -> dict:
    print(f"[call_search_kb] TOOL_SERVER_URL={TOOL_SERVER_URL}", flush=True)

    data = post_with_retry(
        f"{TOOL_SERVER_URL}/tools/search_kb",
        {
            "query": query,
            "top_k": top_k,
        },
    )

    return {
        "results": data.get("results", [])
    }


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
    #status: str | None = None,
    #tags: list[str] | None = None,
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
    data = response.json()
    return{
        "results": data.get("results", []),
    }
    #return response.json()


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

def post_with_retry(url: str, payload: dict, retries: int = 3) -> dict:
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=60,
            )

            print(f"[tool_call] status={response.status_code}", flush=True)
            print(f"[tool_call] body={response.text[:1000]}", flush=True)

            response.raise_for_status()
            return response.json()

        except Exception as e:
            last_error = e
            print(f"[tool_call] attempt={attempt} error={repr(e)}", flush=True)

            if attempt < retries:
                time.sleep(2 ** attempt)

    raise last_error

if __name__ == "__main__":
    result = call_search_kb("VPN authentication failed", top_k=3)
    print(result)