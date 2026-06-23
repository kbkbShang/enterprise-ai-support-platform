import json
from pathlib import Path

TICKETS_PATH = Path("data/tickets/tickets.json")

MOCK_TEMPLATES = [
    (
        "VPN connection drops frequently",
        "User reports intermittent VPN disconnections.",
        ["vpn", "network"],
        "User updated VPN client and switched VPN region."
    ),
    (
        "VPN client not launching",
        "VPN application closes immediately after startup.",
        ["vpn", "software"],
        "VPN client was reinstalled."
    ),
    (
        "SSO login redirects to blank page",
        "User cannot complete SSO login.",
        ["sso", "browser"],
        "Browser cache was cleared."
    ),
    (
        "SSO access denied",
        "User receives access denied error.",
        ["sso", "permissions"],
        "User was added to the correct group."
    ),
    (
        "MFA code expired",
        "User MFA code expires before verification.",
        ["mfa", "authentication"],
        "User synchronized device time."
    ),
    (
        "Password reset email not received",
        "User requested password reset but no email arrived.",
        ["password", "email"],
        "Mail filters were updated."
    ),
    (
        "License server unavailable",
        "Engineering software cannot obtain license.",
        ["license", "software"],
        "License service restarted."
    ),
    (
        "Software installation blocked",
        "Approved software installation fails.",
        ["software", "permissions"],
        "Admin privileges granted temporarily."
    ),
    (
        "Shared drive missing",
        "Project shared drive not visible.",
        ["shared-drive", "permissions"],
        "User added to correct security group."
    ),
    (
        "Remote desktop authentication failure",
        "Remote workstation login fails.",
        ["remote-desktop", "authentication"],
        "Credentials were reset."
    ),
    (
        "Mailbox synchronization delay",
        "Outlook inbox not updating.",
        ["email"],
        "Mailbox profile recreated."
    ),
]

def load_tickets():
    with open(TICKETS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tickets(tickets):
    with open(TICKETS_PATH, "w", encoding="utf-8") as f:
        json.dump(tickets, f, indent=2)


def generate_tickets():
    tickets = load_tickets()

    next_id = len(tickets) + 1

    while len(tickets) < 50:

        template = MOCK_TEMPLATES[(next_id - 1) % len(MOCK_TEMPLATES)]

        title, description, tags, resolution = template

        ticket = {
            "ticket_id": f"TCK-{next_id:04d}",
            "title": title,
            "description": description,
            "status": "resolved",
            "priority": "medium",
            "tags": tags,
            "resolution": resolution,
        }

        tickets.append(ticket)
        next_id += 1

    save_tickets(tickets)

    print(f"Total {len(tickets)} tickets")


if __name__ == "__main__":
    generate_tickets()