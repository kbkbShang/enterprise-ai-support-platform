import json
import os
import time
import logging

from dotenv import load_dotenv
from google.genai import types
from pydantic import ValidationError

from src.agent_api.response_schemas import AgentResponse
from src.agent_api.tools_client import (
    call_search_kb,
    call_get_kb_doc,
    call_search_tickets,
    call_create_ticket_draft,
)

from src.llm.gateway import generate_content
from src.llm.gateway import generate_structured_content

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"

logger = logging.getLogger("agent")
logging.basicConfig(level=logging.INFO)

_last_retry_count = 0


def search_kb(query: str, top_k: int = 3) -> dict:
    """Search internal knowledge base articles.

    Args:
        query: User support question.
        top_k: Number of knowledge base chunks to return.
    """
    return call_search_kb(query=query, top_k=top_k)


def get_kb_doc(doc_id: str) -> dict:
    """Retrieve the full KB document.

    Args:
        doc_id: Document ID returned by search_kb.
    """
    return call_get_kb_doc(doc_id)


def search_tickets(
    query: str,
    status: str | None = "resolved",
    tags: list[str] | None = None,
    top_k: int = 3,
) -> dict:
    """Search historical support tickets.

    Args:
        query: User support question.
        status: Optional ticket status filter.
        tags: Optional ticket tags filter, such as vpn, sso, mfa, license, permission, etc.
        top_k: Number of tickets to return.
    """
    return call_search_tickets(
        query=query,
        status=status,
        tags=tags,
        top_k=top_k,
    )


def create_ticket_draft(
    title: str,
    description: str,
    priority: str = "medium",
    tags: list[str] | None = None,
) -> dict:
    """Create a support ticket draft.

    Args:
        title: Draft ticket title.
        description: Draft ticket description.
        priority: Ticket priority: low, medium, high, or critical.
        tags: Ticket tags.
    """
    return call_create_ticket_draft(
        title=title,
        description=description,
        priority=priority,
        tags=tags or [],
    )


def extract_json_text(text: str) -> str:
    text = text.strip()

    if "```json" in text:
        start = text.find("```json") + len("```json")
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()

    if "```" in text:
        start = text.find("```") + len("```")
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return text[start:end + 1].strip()

    return text


def is_retryable_gemini_error(error: Exception) -> bool:
    error_text = str(error)

    return (
        "503 UNAVAILABLE" in error_text
        or "429 RESOURCE_EXHAUSTED" in error_text
        or "RESOURCE_EXHAUSTED" in error_text
        or "currently experiencing high demand" in error_text
    )

def log_agent_response(query: str, result: dict):
    metadata = result.get("metadata", {})
    ticket_draft = result.get("ticket_draft", {})

    structured_log = {
        "event": "agent_response",
        "query": query,
        "tool_calls": result.get("tool_calls", []),
        "citation_count": metadata.get("citation_count", 0),
        "ticket_created": ticket_draft.get("created", False),
        "latency_ms": metadata.get("latency_ms", 0),
        "retry_count": metadata.get("retry_count", 0),
        "confidence": result.get("confidence", 0.0),
        "model": metadata.get("model"),
    }

    logger.info(json.dumps(structured_log, ensure_ascii=True))

SYSTEM_INSTRUCTION = """
You are an enterprise IT support agent.

Tool routing rules:

1. For any user support question, call search_kb first unless the user explicitly asks only to search historical tickets or only to create a ticket draft.

2. If the user asks for setup steps, troubleshooting, policy, common errors, escalation, access, login, permission, license, software, VPN, SSO, MFA, password, or installation help, call search_kb first.

3. If search_kb returns relevant chunks but the user asks for a complete policy, full guide, full document, all sections, or broader context, call get_kb_doc using the doc_id from the most relevant search_kb result.

4. If the user asks for similar previous cases, resolved examples, past tickets, historical tickets, or historical resolutions, call search_tickets. If the question also needs knowledge-base guidance, call search_kb as well.

5. If the user explicitly asks to create a ticket draft, call create_ticket_draft.

6. If search_kb does not provide enough relevant evidence to answer confidently, call create_ticket_draft.

Evidence and citation rules:

- Prefer answering from retrieved evidence only.
- Use get_kb_doc only to obtain additional context for answer generation.
- Even when get_kb_doc is used, citations must come from search_kb results.
- Citations must include the original doc_id, chunk_id, and quote from retrieved search_kb chunks.
- Do not create new citations from the full document content.
- Do not output citations with an empty chunk_id.
- Do not include a "Citations" section inside the answer.
- Put citations only in the top-level citations array.
- When citing evidence, use only information returned by the tools.
- For troubleshooting questions, if search_kb returns one or more results, answer using the KB results with citations. Do not create a ticket draft unless the user explicitly asks to create a ticket, or the KB results explicitly say escalation is required after the user has already tried all recommended steps.

Safety and grounding rules:

- Do not invent facts, procedures, citations, draft IDs, or unsupported solutions.
- Keep answers concise, actionable, and grounded in retrieved evidence.

Ticket rules:

- If there is not enough evidence to answer confidently, create a ticket draft.
- You must never claim a ticket draft was created unless you actually called create_ticket_draft.
- If ticket_draft.created is true, the draft_id must come from the create_ticket_draft tool response.
- Never invent draft_id values.
- If create_ticket_draft was not called, ticket_draft.created must be false and draft_id must be null.
- For unresolved issues where a ticket draft is created, set confidence to 0.0 because no knowledge-base evidence was found.
- If you suggest creating a ticket draft for an unresolved issue, you must actually call create_ticket_draft to create the draft ticket and return the created draft_id.
- If the user asks to find similar resolved tickets, historical tickets, previous cases, or past resolutions, call search_tickets. If search_tickets fails or returns no useful results, do not create a ticket draft unless the user explicitly asks to create one. Return a concise message explaining that no similar resolved ticket was found or that ticket search is unavailable.

Out-of-scope and special cases:

- If the user explicitly asks to find, compare, or summarize historical tickets, call search_tickets first. You do not need to call search_kb unless the user also asks for knowledge-base guidance.
- If the user explicitly asks to create, draft, submit, or escalate a support ticket, call create_ticket_draft directly.
- If the user asks a question unrelated to enterprise IT support, do not answer from general knowledge. Politely state that the request is outside the IT support knowledge base. If it still appears to require support follow-up, create a ticket draft.
- If the user asks for casual conversation, opinions, coding help, math, general knowledge, or non-IT topics, do not use KB citations. Explain that this agent is designed for enterprise IT support.

Output rules:

- Return only valid JSON.
- Do not include markdown code fences.
- Return exactly this JSON shape:

{
  "answer": "...",
  "citations": [
    {
      "doc_id": "...",
      "chunk_id": "...",
      "quote": "..."
    }
  ],
  "confidence": 0.0,
  "next_actions": [
    "..."
  ],
  "ticket_draft": {
    "created": false,
    "draft_id": null
  }
}
"""


def generate_content_with_retry(query: str, max_retries: int = 3):
    global _last_retry_count

    _last_retry_count = 0

    return generate_structured_content(
        contents=query,
        schema=AgentResponse,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[
                search_kb,
                get_kb_doc,
                search_tickets,
                create_ticket_draft,
            ],
        ),
        model=MODEL_NAME,
        max_retries=max_retries,
    )


def extract_tool_calls(response) -> list[str]:
    tool_calls = []

    history = getattr(response, "automatic_function_calling_history", []) or []

    for item in history:
        parts = getattr(item, "parts", []) or []

        for part in parts:
            function_call = getattr(part, "function_call", None)

            if function_call:
                tool_calls.append(function_call.name)

    return tool_calls


def build_metadata(
    start_time: float,
    tool_calls: list[str],
    result: dict | None = None,
) -> dict:
    result = result or {}

    citations = result.get("citations", [])

    ticket_created = (
        result
        .get("ticket_draft", {})
        .get("created", False)
    )

    return {
        "latency_ms": int((time.time() - start_time) * 1000),
        "retry_count": _last_retry_count,
        "tool_call_count": len(tool_calls),
        "citation_count": len(citations),
        "ticket_created": ticket_created,
        "model": MODEL_NAME,
    }


def build_fallback_response(
    answer: str,
    start_time: float,
    tool_calls: list[str],
    next_actions: list[str] | None = None,
) -> dict:
    fallback = {
        "answer": answer,
        "citations": [],
        "confidence": 0.0,
        "next_actions": next_actions or [],
        "ticket_draft": {
            "created": False,
            "draft_id": None,
        },
        "tool_calls": tool_calls,
    }

    fallback["metadata"] = build_metadata(
        start_time=start_time,
        tool_calls=tool_calls,
        result=fallback,
    )

    return fallback


def run_gemini_agent(query: str) -> dict:
    start_time = time.time()
    tool_calls = []

    try:
        validated_response, raw_response = generate_content_with_retry(query)

        tool_calls = extract_tool_calls(raw_response)
        
        # 现在 validated_response 已经是 AgentResponse，不是 Gemini raw response
        result = validated_response.model_dump()
        result["tool_calls"] = tool_calls
        result["metadata"] = build_metadata(
            start_time=start_time,
            tool_calls=tool_calls,
            result=result,
        )

        log_agent_response(query, result)
        
        return result

    except Exception as e:
        fallback = build_fallback_response(
            answer=f"Agent failed to generate a response: {str(e)}",
            start_time=start_time,
            tool_calls=tool_calls,
            next_actions=[
                "Try again or create a support ticket manually."
            ],
        )
        log_agent_response(query, fallback)
        return fallback