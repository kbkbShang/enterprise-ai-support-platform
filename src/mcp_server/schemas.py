from pydantic import BaseModel, Field

class SearchKBRequest(BaseModel):
    query: str = Field(..., description="User query for searching the knowledge base")
    top_k: int = Field(default=5, description="Number of KB chunks to return")


class GetKBDocRequest(BaseModel):
    doc_id: str = Field(..., description="Knowledge base document ID")


class SearchTicketsRequest(BaseModel):
    query: str
    status: str | None = None
    tags: list[str] | None = None
    top_k: int = 3


class CreateTicketDraftRequest(BaseModel):
    title: str = Field(..., description="Draft ticket title")
    description: str = Field(..., description="Draft ticket description")
    priority: str = Field(default="medium", description="Ticket priority")
    tags: list[str] = Field(default_factory=list, description="Ticket tags")