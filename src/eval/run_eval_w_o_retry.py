import json
from pathlib import Path

import requests


BASE_DIR = Path(__file__).parent

TEST_CASES_PATH = BASE_DIR / "test_cases.json"
REPORT_PATH = BASE_DIR / "report.json"

CHAT_ENDPOINT = "http://localhost:8000/chat"


def is_api_error(agent_result: dict) -> bool:
    answer = agent_result.get("answer", "")

    return (
        "503 UNAVAILABLE" in answer
        or "429 RESOURCE_EXHAUSTED" in answer
        or "RESOURCE_EXHAUSTED" in answer
        or "model is currently experiencing high demand" in answer
    )

def validate_citations(agent_result: dict) -> tuple[bool, int]:
    citations = agent_result.get("citations", [])

    if not citations:
        return False, 0

    valid_count = 0

    for citation in citations:
        doc_id = citation.get("doc_id")
        chunk_id = citation.get("chunk_id")
        quote = citation.get("quote")

        if doc_id and chunk_id and quote:
            valid_count += 1

    all_valid = valid_count == len(citations)

    return all_valid, valid_count


def run_eval():
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    results = []

    passed = 0
    api_errors = 0
    logic_failures = 0

    for case in test_cases:
        response = requests.post(
            CHAT_ENDPOINT,
            json={
                "query": case["query"],
                "session_id": case["id"],
            },
            timeout=60,
        )

        agent_result = response.json()

        api_error = is_api_error(agent_result)

        actual_tools = set(agent_result.get("tool_calls", []))
        expected_tools = set(case["expected_tools"])

        tools_match = expected_tools.issubset(actual_tools)

        citations_exist = len(agent_result.get("citations", [])) > 0
        citations_match = citations_exist == case["should_have_citations"]

        citation_valid, citation_valid_count = validate_citations(agent_result)

        citation_validation_match = (
            citation_valid if case["should_have_citations"] else not citations_exist
        )

        ticket_created = (
            agent_result
            .get("ticket_draft", {})
            .get("created", False)
        )

        ticket_match = ticket_created == case["should_create_ticket"]

        test_pass = (
            not api_error
            and tools_match
            and citations_match
            and citation_validation_match
            and ticket_match
        )

        if test_pass:
            passed += 1
        elif api_error:
            api_errors += 1
        else:
            logic_failures += 1

        results.append(
            {
                "id": case["id"],
                "query": case["query"],
                "passed": test_pass,
                "api_error": api_error,
                "tools_match": tools_match,
                "citations_match": citations_match,
                "citation_valid": citation_valid,
                "ticket_match": ticket_match,
                "actual_tools": list(actual_tools),
                "expected_tools": list(expected_tools),
                "citation_valid_count": citation_valid_count,
                "citation_count": len(agent_result.get("citations", [])),
                "answer_preview": agent_result.get("answer", "")[:500],
                "next_actions": agent_result.get("next_actions", []),
                "ticket_draft": agent_result.get("ticket_draft", {}),
            }
        )

    report = {
        "total_tests": len(test_cases),
        "passed": passed,
        "failed": len(test_cases) - passed,
        "api_errors": api_errors,
        "logic_failures": logic_failures,
        "pass_rate": round(passed / len(test_cases), 2),
        "logic_pass_rate": round(
            passed / (len(test_cases) - api_errors),
            2
        ) if len(test_cases) > api_errors else 0.0,
        "results": results,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Pass Rate: {report['pass_rate']}")
    print(f"API Errors: {api_errors}")
    print(f"Logic Failures: {logic_failures}")
    print(f"Logic Pass Rate: {report['logic_pass_rate']}")
    print("=" * 60)


if __name__ == "__main__":
    run_eval()