from fastapi import FastAPI

from src.rag.retriever import search_kb as rag_search_kb
from src.tickets.draft import create_ticket_draft
from src.rag.firestore_kb_store import get_kb_doc as get_kb_doc_firestore
from src.tickets.search import search_tickets as ticket_search

from src.mcp_server.schemas import (
    SearchKBRequest,
    GetKBDocRequest,
    SearchTicketsRequest,
    CreateTicketDraftRequest,
)

from src.rag.retriever import get_collection

app = FastAPI(title="Enterprise AI Support Agent", description="API for MCP Gemini Support Agent", version="1.0.0")

## This is a mock implementation of the tool server. In a real implementation, this would connect to a knowledge base and ticketing system.
@app.get("/health")
def health():
    collection = get_collection()
    return {
        "status": "ok",
        "service": "tool_server",
        "storage": "firestore",
        "retrieval": "chroma",
        "chroma_count": collection.count(),
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
    record = get_kb_doc_firestore(request.doc_id)

    if not record:
        return {
            "tool": "get_kb_doc",
            "doc_id": request.doc_id,
            "found": False,
            "document": None,
        }

    return {
        "tool": "get_kb_doc",
        "doc_id": request.doc_id,
        "found": True,
        "document": {
            "doc_id": record["doc_id"],
            "title": record["title"],
            "content": record["text"],
            "metadata": {
                "source_path": record["source_path"]
            }
        }
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
