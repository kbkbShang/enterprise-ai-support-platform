import json
from pathlib import Path


TICKETS_PATH = Path("data/tickets/tickets.json")


def load_tickets() -> list[dict]:
    """
    Load historical support tickets from JSON file.
    """
    if not TICKETS_PATH.exists():
        return []

    with open(TICKETS_PATH, "r", encoding="utf-8") as f:
        tickets = json.load(f)

    return tickets


if __name__ == "__main__":
    tickets = load_tickets()

    print(f"Loaded {len(tickets)} tickets")

    for ticket in tickets[:3]:
        print("=" * 60)
        print(ticket["ticket_id"])
        print(ticket["title"])
        print(ticket["status"])