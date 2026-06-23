from src.agent_api.tools_client import (
    call_search_kb,
    call_search_tickets,
    call_create_ticket_draft,
)


def run_agent(query: str) -> dict:
    """
    Simple rule-based agent flow before Gemini function calling.
    """

    kb_response = call_search_kb(query=query, top_k=3)
    kb_results = kb_response.get("results", [])

    ticket_response = call_search_tickets(query=query, status="resolved", top_k=3)
    ticket_results = ticket_response.get("results", [])

    citations = []

    for item in kb_results:
        citations.append(
            {
                "doc_id": item["doc_id"],
                "chunk_id": item["chunk_id"],
                "quote": item["text"][:300],
            }
        )

    has_evidence = (
        len(kb_results) > 0
        and kb_results[0]["score"] > 0.55
    )

    if has_evidence:
        answer = build_answer_from_evidence(query, kb_results, ticket_results)

        return {
            "answer": answer,
            "citations": citations,
            "confidence": kb_results[0]["score"],
            "next_actions": extract_next_actions(kb_results),
            "ticket_draft": {
                "created": False,
                "draft_id": None,
            },
        }

    draft = call_create_ticket_draft(
        title=f"Unresolved support request: {query[:50]}",
        description=f"User asked: {query}. No sufficient KB evidence was found.",
        priority="medium",
        tags=["unresolved"],
    )

    return {
        "answer": "I could not find enough evidence in the knowledge base to confidently answer this request. I created a ticket draft for IT support review.",
        "citations": [],
        "confidence": 0.0,
        "next_actions": ["Wait for IT support follow-up"],
        "ticket_draft": {
            "created": True,
            "draft_id": draft.get("draft_id"),
        },
    }


def build_answer_from_evidence(query: str, kb_results: list[dict], ticket_results: list[dict]) -> str:
    """
    Build a simple grounded answer from retrieved KB and ticket evidence.
    Later this will be replaced by Gemini generation.
    """
    top_kb = kb_results[0]

    answer = (
        f"Based on the knowledge base article '{top_kb['doc_id']}', "
        f"the most relevant guidance is from the section '{top_kb['heading']}'. "
        f"{top_kb['text']}"
    )

    if ticket_results:
        top_ticket = ticket_results[0]
        answer += (
            f"\n\nA similar historical ticket ({top_ticket['ticket_id']}) was resolved by: "
            f"{top_ticket['resolution']}"
        )

    return answer


def extract_next_actions(kb_results: list[dict]) -> list[str]:
    """
    Extract simple next actions from the top KB result.
    """
    if not kb_results:
        return []

    text = kb_results[0]["text"]

    actions = []

    if "restart" in text.lower():
        actions.append("Restart the related client or application")

    if "mfa" in text.lower():
        actions.append("Complete MFA approval")

    if "support ticket" in text.lower():
        actions.append("Create a support ticket if the issue remains unresolved")

    if not actions:
        actions.append("Follow the steps in the cited knowledge base section")

    return actions