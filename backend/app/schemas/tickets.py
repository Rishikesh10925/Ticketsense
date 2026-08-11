from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    subject: str = Field(min_length=4, max_length=255)
    description: str = Field(min_length=10, max_length=10000)
    category: str | None = None
    product: str | None = None
    severity: str | None = None
    environment: str | None = None
    error_message: str | None = None


class Evidence(BaseModel):
    title: str
    excerpt: str
    score: float
    source: str


class TicketPublic(BaseModel):
    id: UUID
    subject: str
    description: str
    status: str
    priority: str | None
    sentiment: str | None
    department_id: UUID | None
    ai_draft_reply: str | None
    confidence_score: float | None
    analysis: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TicketAction(BaseModel):
    action: str
    response: str | None = None
    reason: str | None = None


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    resolved: bool = True
