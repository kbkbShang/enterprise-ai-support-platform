import os
import requests
from dotenv import load_dotenv
import time
import google.auth.transport.requests
import google.oauth2.id_token


load_dotenv()

TOOL_SERVER_URL = os.getenv("TOOL_SERVER_URL", "http://localhost:7001")

def get_tool_server_auth_headers() -> dict:
    auth_request = google.auth.transport.requests.Request()
    token = google.oauth2.id_token.fetch_id_token(
        auth_request,
        TOOL_SERVER_URL,
    )

    return {
        "Authorization": f"Bearer {token}",
    }

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
    return post_with_retry(
        f"{TOOL_SERVER_URL}/tools/get_kb_doc",
        {
            "doc_id": doc_id,
        },
    )


def call_search_tickets(query: str, status=None, tags=None, top_k: int = 3) -> dict:
    data = post_with_retry(
        f"{TOOL_SERVER_URL}/tools/search_tickets",
        {
            "query": query,
            "status": status,
            "tags": tags,
            "top_k": top_k,
        },
    )

    return {
        "results": data.get("results", [])
    }


def call_create_ticket_draft(
    title: str,
    description: str,
    priority: str = "medium",
    tags: list[str] | None = None,
) -> dict:
    return post_with_retry(
        f"{TOOL_SERVER_URL}/tools/create_ticket_draft",
        {
            "title": title,
            "description": description,
            "priority": priority,
            "tags": tags or [],
        },
    )

def post_with_retry(url: str, payload: dict, retries: int = 3) -> dict:
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            headers = get_tool_server_auth_headers()
            headers["Connection"] = "close"

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=(30, 180),
            )

            print(f"[tool_call] status={response.status_code}", flush=True)
            print(f"[tool_call] body={response.text[:1000]}", flush=True)

            response.raise_for_status()
            return response.json()

        except Exception as e:
            last_error = e
            print(f"[tool_call] attempt={attempt} error={repr(e)}", flush=True)

            if attempt < retries:
                time.sleep(5 * attempt)

    raise last_error

if __name__ == "__main__":
    result = call_search_kb("VPN authentication failed", top_k=3)
    print(result)