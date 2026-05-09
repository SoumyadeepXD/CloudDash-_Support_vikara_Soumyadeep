from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
import uuid

AgentType = Literal["triage", "technical", "billing", "escalation"]
Priority = Literal["low", "medium", "high", "critical"]

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent: Optional[str] = None

class ExtractedEntities(BaseModel):
    customer_id: Optional[str] = None
    plan: Optional[str] = None
    issue_type: Optional[str] = None
    product_refs: List[str] = []
    sentiment: Optional[Literal["positive", "neutral", "negative", "frustrated"]] = None
    urgency: Optional[Priority] = None

class ConversationState(BaseModel):
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = []
    current_agent: str = "triage"
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    secondary_intent: Optional[str] = None
    resolved: bool = False
    escalated: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RetrievedChunk(BaseModel):
    article_id: str
    title: str
    category: str
    content: str
    score: float
    source_url: Optional[str] = None

class AgentResponse(BaseModel):
    content: str
    agent: str                              # str not AgentType — avoids crash on invalid values
    citations: List[RetrievedChunk] = []
    suggested_next_agent: Optional[str] = None   # str not AgentType — validated in orchestrator
    confidence: float = 1.0
    requires_handover: bool = False
    handover_reason: Optional[str] = None
    metadata: dict = {}

class HandoverPayload(BaseModel):
    handover_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_agent: str
    target_agent: str
    reason: str
    conversation_state: ConversationState
    context_summary: str
    priority: Priority = "medium"
    entities: ExtractedEntities
