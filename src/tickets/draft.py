import json
from datetime import datetime, timezone
from pathlib import Path

DRAFTS_PATH = Path("data/tickets/ticket_drafts.json")

def load_ticket_drafts() -> list[dict]:
    """
    Load ticket drafts from JSON file.
    """
    if not DRAFTS_PATH.exists():
        return []
        

    with open(DRAFTS_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []
    
def save_ticket_drafts(drafts: list[dict]):
    """
    Save ticket drafts to JSON file.
    """
    # Ensure the parent directory exists, if not, create it
    DRAFTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(DRAFTS_PATH, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2)

def generate_draft_id(drafts: list[dict]) -> str:
    """
    Generate the next draft id.
    Example: DRF-0001, DRF-0002
    """
    next_id = len(drafts) + 1
    return f"DRF-{next_id:04d}"

def create_ticket_draft(
        title: str, 
        description: str, 
        priority: str = "medium",
        tags: list[str] | None = None,
) -> dict:
    """
    Create and save a new ticket draft.
    """
    drafts = load_ticket_drafts()

    draft_id = generate_draft_id(drafts)

    new_draft = {
        "draft_id": draft_id,
        "title": title,
        "description": description,
        "priority": priority,
        "tags": tags or [],
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    drafts.append(new_draft)
    save_ticket_drafts(drafts)

    return {
        "draft_id": draft_id,
        "saved": True,
        "record": new_draft,
    }

if __name__ == "__main__":
    result = create_ticket_draft(
        title="VPN still not working",
        description="User cannot connect to VPN after restarting the client and completing MFA.",
        priority="high",
        tags=["vpn", "authentication"],
    )

    print(result)
