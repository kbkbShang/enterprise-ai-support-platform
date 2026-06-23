from src.tickets.loader import load_tickets


def tokenize(text: str) -> list[str]:
    """
    Simple tokenizer for keyword matching.
    """
    text = text.lower()

    for ch in [".", ",", ":", ";", "(", ")", "[", "]", "\"", "'", "/", "\\", "-", "_"]:
        text = text.replace(ch, " ")

    return [word for word in text.split() if word]


def ticket_to_search_text(ticket: dict) -> str:
    """
    Combine important ticket fields into one searchable text.
    """
    return " ".join(
        [
            ticket.get("title", ""),
            ticket.get("description", ""),
            ticket.get("resolution", ""),
            " ".join(ticket.get("tags", [])),
        ]
    )


def score_ticket(query: str, ticket: dict) -> float:
    """
    Score a ticket by keyword overlap.
    """
    query_tokens = set(tokenize(query))
    ticket_tokens = set(tokenize(ticket_to_search_text(ticket)))

    if not query_tokens:
        return 0.0

    overlap = query_tokens.intersection(ticket_tokens)

    return len(overlap) / len(query_tokens)


def search_tickets(
    query: str,
    status: str | None = None,
    tags: list[str] | None = None,
    top_k: int = 5,
) -> list[dict]:
    """
    Search historical support tickets by query, optional status, and optional tags.
    """
    tickets = load_tickets()
    scored_results = []

    for ticket in tickets:
        # Check if ticket matches the status filter (if provided)
        if status and ticket.get("status") != status:
            continue

        # Check if ticket has at least one of the required tags (if tags filter is provided)
        if tags:
            ticket_tags = set(ticket.get("tags", []))
            required_tags = set(tags)

            if not required_tags.intersection(ticket_tags):
                continue

        score = score_ticket(query, ticket)

        if score > 0:
            scored_results.append(
                {
                    "ticket_id": ticket["ticket_id"],
                    "title": ticket["title"],
                    "status": ticket["status"],
                    "priority": ticket["priority"],
                    "tags": ticket["tags"],
                    "score": round(score, 4),
                    "resolution": ticket["resolution"],
                }
            )

    scored_results.sort(key=lambda x: x["score"], reverse=True)

    return scored_results[:top_k]


if __name__ == "__main__":
    results = search_tickets(
        query="VPN authentication failed",
        status="resolved",
        tags=["vpn"],
        top_k=3,
    )

    print(f"Found {len(results)} tickets")

    for result in results:
        print("=" * 60)
        print(result["ticket_id"], result["score"])
        print(result["title"])
        print(result["resolution"])