import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000/chat")
API_BASE_URL = API_URL.replace("/chat", "")

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

tab_chat, tab_dashboard = st.tabs(["💬 Chat", "📊 Dashboard"])

with tab_chat:
    query = st.text_input("Enter your support question")

    if st.button("Submit"):
        response = requests.post(
            API_URL,
            json={
                "query": query,
                "session_id": "streamlit-demo",
            },
            timeout=120,
        )

        result = response.json()

        st.subheader("Answer")
        st.write(result["answer"])

        st.subheader("Confidence")
        st.write(result["confidence"])

        st.subheader("Tool Calls")
        st.json(result.get("tool_calls", []))

        st.subheader("Citations")
        for citation in result.get("citations", []):
            st.info(
                f"""
                Document: {citation['doc_id']}

                Chunk: {citation['chunk_id']}

                {citation['quote']}
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

        col1.metric(
            "Firestore",
            checks.get("firestore", {}).get("status", "unknown"),
        )

        col2.metric(
            "Tool Server",
            checks.get("tool_server", {}).get("status", "unknown"),
        )

        col3.metric(
            "Pub/Sub",
            checks.get("pubsub", {}).get("status", "unknown"),
        )

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

        col1.metric(
            "Tickets Created",
            agent.get("ticket_created_count", 0),
        )

        col2.metric(
            "Total Citations",
            agent.get("total_citations", 0),
        )

        col3.metric(
            "Avg Citations / Job",
            agent.get("avg_citations_per_completed_job", 0),
        )

    except Exception as e:
        st.error(f"Failed to load dashboard metrics: {e}")