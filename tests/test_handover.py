import pytest
import os
from models.state import ConversationState, AgentType, ExtractedEntities
from handover.protocol import create_handover, validate_handover
from handover.audit_log import log_handover

def test_create_handover():
    state = ConversationState()
    payload = create_handover(
        source_agent="triage",
        target_agent="escalation",
        reason="User angry",
        state=state,
        context_summary="User needs help.",
        priority="high"
    )
    assert payload.source_agent == "triage"
    assert payload.target_agent == "escalation"
    assert payload.priority == "high"

def test_validate_handover():
    state = ConversationState()
    payload = create_handover(
        source_agent="triage",
        target_agent="escalation",
        reason="Test",
        state=state,
        context_summary="Test"
    )
    assert validate_handover(payload) == True

def test_audit_log_written():
    state = ConversationState()
    payload = create_handover("triage", "technical", "reason", state, "summary")
    log_handover(payload)
    
    assert os.path.exists("logs/handover_audit.jsonl")
    with open("logs/handover_audit.jsonl", "r") as f:
        content = f.read()
        assert payload.handover_id in content
