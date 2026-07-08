import os
import time
import requests
import streamlit as st


API_BASE_URL = os.getenv(
    "API_URL",
    "http://localhost:8000",
).replace("/chat", "").rstrip("/")


st.set_page_config(
    page_title="Enterprise AI Support Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Enterprise AI Support Agent")

with st.sidebar:
    st.header("System Info")
    st.write("Gemini 2.5 Flash")
    st.write("FastAPI + Pub/Sub + Worker")
    st.write("Firestore + ChromaDB")
    st.write("LLM Gateway + SSE")
    st.caption(f"API: {API_BASE_URL}")

tab_chat, tab_dashboard = st.tabs(["💬 Chat", "📊 Dashboard"])


with tab_chat:
    query = st.text_input("Enter your support question")

    session_id = st.text_input(
        "Session ID (optional)",
        value="",
        placeholder="Leave empty to auto-generate",
    )

    if st.button("Submit"):
        if not query.strip():
            st.warning("Please enter a support question.")
            st.stop()

        payload = {
            "query": query,
            "session_id": session_id.strip() or None,
        }

        with st.spinner("Creating support job..."):
            response = requests.post(
                f"{API_BASE_URL}/support-jobs",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            job = response.json()

        job_id = job["job_id"]

        st.info(f"Job created: {job_id}")

        st.subheader("Progress Events")
        progress_box = st.empty()

        events = []

        try:
            with requests.get(
                f"{API_BASE_URL}/support-jobs/{job_id}/events",
                stream=True,
                timeout=(10, 600),
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    if not line.startswith("data: "):
                        continue

                    event_text = line.replace("data: ", "", 1)
                    events.append(event_text)

                    progress_box.code("\n".join(events[-15:]))

                    if '"event": "job_finished"' in event_text:
                        break

        except Exception as e:
            st.warning(f"Event stream ended or failed: {e}")

        with st.spinner("Loading final result..."):
            response = requests.get(
                f"{API_BASE_URL}/support-jobs/{job_id}/result",
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "completed":
            st.error(data.get("error") or f"Job status: {data.get('status')}")
            st.stop()

        result = data.get("result") or {}

        st.subheader("Answer")
        st.write(result.get("answer", ""))

        st.subheader("Confidence")
        st.write(result.get("confidence", 0))

        st.subheader("Tool Calls")
        st.json(result.get("tool_calls", []))

        st.subheader("Ticket Draft")
        st.json(result.get("ticket_draft", {}))

        st.subheader("Citations")
        citations = result.get("citations", [])

        if not citations:
            st.write("No citations returned.")
        else:
            for citation in citations:
                st.info(
                    f"""
                    Document: {citation.get('doc_id')}

                    Chunk: {citation.get('chunk_id')}

                    {citation.get('quote')}
                    """
                )


with tab_dashboard:
    st.header("System Dashboard")

    try:
        ready = requests.get(
            f"{API_BASE_URL}/ready",
            timeout=30,
        ).json()

        metrics = requests.get(
            f"{API_BASE_URL}/metrics",
            timeout=30,
        ).json()

        st.subheader("Service Readiness")

        col1, col2, col3 = st.columns(3)

        checks = ready.get("checks", {})

        col1.metric("Firestore", checks.get("firestore", {}).get("status", "unknown"))
        col2.metric("Tool Server", checks.get("tool_server", {}).get("status", "unknown"))
        col3.metric("Pub/Sub", checks.get("pubsub", {}).get("status", "unknown"))

        st.subheader("Jobs")

        jobs = metrics.get("jobs", {})

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Jobs", jobs.get("total", 0))
        col2.metric("Completed", jobs.get("completed", 0))
        col3.metric("Failed", jobs.get("failed", 0))
        col4.metric("Success Rate", f"{jobs.get('success_rate', 0)}%")

        st.subheader("Performance")

        performance = metrics.get("performance", {})

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Avg Queue Latency",
            f"{performance.get('avg_queue_latency_ms', 0)} ms",
        )

        col2.metric(
            "Avg Processing Latency",
            f"{performance.get('avg_processing_latency_ms', 0)} ms",
        )

        col3.metric(
            "Avg LLM Latency",
            f"{performance.get('avg_llm_latency_ms', 0)} ms",
        )

        st.subheader("Agent Metrics")

        agent = metrics.get("agent", {})

        col1, col2, col3 = st.columns(3)

        col1.metric("Tickets Created", agent.get("ticket_created_count", 0))
        col2.metric("Total Citations", agent.get("total_citations", 0))
        col3.metric(
            "Avg Citations / Job",
            agent.get("avg_citations_per_completed_job", 0),
        )

    except Exception as e:
        st.error(f"Failed to load dashboard metrics: {e}")