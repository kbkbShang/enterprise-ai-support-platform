import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000/chat")

st.set_page_config(
    page_title="Enterprise AI Support Agent",
    page_icon="🤖",
)

st.title("🤖 Enterprise AI Support Agent")

query = st.text_input(
    "Enter your support question"
)

with st.sidebar:

    st.header("System Info")

    st.write(
        "Gemini 2.5 Flash"
    )

    st.write(
        "Dockerized Deployment"
    )

    st.write(
        "FastAPI + Function Calling"
    )

if st.button("Submit"):

    response = requests.post(
        API_URL,
        json={
            "query": query,
            "session_id": "streamlit-demo"
        }
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
    