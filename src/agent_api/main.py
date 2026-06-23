from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os

# from src.agent_api.agent import run_agent
# from src.agent_api.gemini_agent_v1 import run_gemini_agent
# from src.agent_api.gemini_agent_v2 import run_gemini_agent
from src.agent_api.gemini_agent_v3 import run_gemini_agent

# This is a skeleton implementation of the MCP Gemini Support Agent API. It defines the API endpoints and data models, but the actual logic for handling chat requests and calling tools is not implemented yet. The tool server URL is configurable via an environment variable.
app = FastAPI(title="MCP Gemini Support Agent API", description="API for MCP Gemini Support Agent", version="1.0.0")

## Configuration
TOOL_SERVER_URL = os.getenv("TOOL_SERVER_URL", "http://localhost:7001")

## Data Models
class ChatRequest(BaseModel):
    query: str
    session_id: str | None = None

@app.get("/")
def root():
    return {
        "message": "Enterprise AI Support Agent is running",
        "docs": "/docs",
        "health": "/health"
    }

## API Endpoints
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "agent_api",
        "tool_server_url": TOOL_SERVER_URL
    }

## This is a mock implementation of the chat endpoint. In a real implementation, this would process the query, call the appropriate tools, and generate a response based on the tool outputs.
@app.post("/chat")
def chat(request: ChatRequest):
    # return run_agent(request.query)
    return run_gemini_agent(request.query)