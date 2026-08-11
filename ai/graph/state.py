from typing import TypedDict


class RetrievedChunk(TypedDict):
    title: str
    chunk_text: str
    distance: float


class TicketState(TypedDict, total=False):
    subject: str
    description: str

    department: str
    priority: str
    sentiment: str

    retrieved_chunks: list[RetrievedChunk]

    draft_reply: str
    confidence_score: float
