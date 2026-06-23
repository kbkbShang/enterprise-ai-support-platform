from fastapi import FastAPI

from src.rag.retriever import search_kb as rag_search_kb
from src.rag.retriever import get_kb_doc as rag_get_kb_doc
from src.tickets.search import search_tickets as ticket_search
from src.tickets.draft import create_ticket_draft

from src.mcp_server.schemas import (
    SearchKBRequest,
    GetKBDocRequest,
    SearchTicketsRequest,
    CreateTicketDraftRequest,
)

app = FastAPI(title="MCP Gemini Support Agent", description="API for MCP Gemini Support Agent", version="1.0.0")

## This is a mock implementation of the tool server. In a real implementation, this would connect to a knowledge base and ticketing system.
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "tool_server",
        "kb_index_exists": False,
        "tickets_readable": False
    }
   
# Tool endpoint for searching the knowledge base. 
# Performs a similarity search in Chroma 
# and returns the top K most relevant chunks. 
# Each chunk includes doc_id, chunk_id, score, heading, and text.
@app.post("/tools/search_kb")
def search_kb(request: SearchKBRequest):

    results = rag_search_kb(
        query=request.query,
        top_k=request.top_k,
    )

    return {
        "tool": "search_kb",
        "query": request.query,
        "top_k": request.top_k,
        "results": results,
    }

# Tool endpoint for retrieving a full KB document by doc_id.
# Returns the document content and metadata (e.g. source path).
@app.post("/tools/get_kb_doc")
def get_kb_doc(request: GetKBDocRequest):

    doc = rag_get_kb_doc(request.doc_id)

    if doc is None:
        return {
            "tool": "get_kb_doc",
            "doc_id": request.doc_id,
            "error": "document not found"
        }

    return {
        "tool": "get_kb_doc",
        **doc
    }

# Tool endpoint for searching historical support tickets.
# Accepts a query string and optional filters (status, tags).
# Returns a list of matching tickets with basic info (ticket_id, title, status, priority).
@app.post("/tools/search_tickets")
def search_tickets(request: SearchTicketsRequest):

    results = ticket_search(
        query=request.query,
        status=request.status,
        tags=request.tags,
        top_k=request.top_k,
    )

    return {
        "tool": "search_tickets",
        "query": request.query,
        "results": results,
    }

# Tool endpoint for creating a new ticket draft.
# Accepts title, description, priority, and tags.   
# Returns the created draft with a unique draft_id and created_at timestamp.
@app.post("/tools/create_ticket_draft")
def create_ticket_draft_api(
    request: CreateTicketDraftRequest
):

    result = create_ticket_draft(
        title=request.title,
        description=request.description,
        priority=request.priority,
        tags=request.tags,
    )

    return {
        "tool": "create_ticket_draft",
        **result
    }
