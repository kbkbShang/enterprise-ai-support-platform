from pydantic import BaseModel, Field


class Citation(BaseModel):
    doc_id: str = Field(default="")
    chunk_id: str = Field(default="")
    quote: str = Field(default="")


class TicketDraftInfo(BaseModel):
    created: bool = Field(default=False)
    draft_id: str | None = Field(default=None)


class AgentResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(default=0.0)
    next_actions: list[str] = Field(default_factory=list)
    ticket_draft: TicketDraftInfo = Field(default_factory=TicketDraftInfo)