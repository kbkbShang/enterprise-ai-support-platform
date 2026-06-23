import json
import time
from pathlib import Path

import requests


BASE_DIR = Path(__file__).parent

TEST_CASES_PATH = BASE_DIR / "smoke_cases.json"
REPORT_PATH = BASE_DIR / "smoke_report.json"

CHAT_ENDPOINT = "http://localhost:8000/chat"


def is_api_error(agent_result: dict) -> bool:
    answer = agent_result.get("answer", "")

    return (
        "503 UNAVAILABLE" in answer
        or "429 RESOURCE_EXHAUSTED" in answer
        or "RESOURCE_EXHAUSTED" in answer
        or "model is currently experiencing high demand" in answer
    )


def call_chat_with_retry(payload: dict, max_retries: int = 3) -> dict:
    last_result = {}

    for attempt in range(max_retries):
        response = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            timeout=60,
        )

        agent_result = response.json()

        if not is_api_error(agent_result):
            return agent_result

        last_result = agent_result
        time.sleep(5 * (attempt + 1))

    return last_result


def run_eval():
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    results = []

    passed = 0
    api_errors = 0
    logic_failures = 0

    for case in test_cases:
        agent_result = call_chat_with_retry(
            {
                "query": case["query"],
                "session_id": case["id"],
            }
        )

        api_error = is_api_error(agent_result)

        actual_tools = set(agent_result.get("tool_calls", []))
        expected_tools = set(case["expected_tools"])

        tools_match = expected_tools.issubset(actual_tools)

        citations_exist = len(agent_result.get("citations", [])) > 0
        citations_match = citations_exist == case["should_have_citations"]

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
                "ticket_match": ticket_match,
                "actual_tools": list(actual_tools),
                "expected_tools": list(expected_tools),
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
    if logic_failures > 0 or api_errors > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    run_eval()