from models.state import ConversationState, HandoverPayload, Priority

def create_handover(
    source_agent: str,
    target_agent: str,
    reason: str,
    state: ConversationState,
    context_summary: str,
    priority: Priority = "medium"
) -> HandoverPayload:
    """Creates a validated HandoverPayload."""
    return HandoverPayload(
        source_agent=source_agent,
        target_agent=target_agent,
        reason=reason,
        conversation_state=state,
        context_summary=context_summary,
        priority=priority,
        entities=state.entities
    )

def validate_handover(payload: HandoverPayload) -> bool:
    """Returns True if the payload is complete and the target agent exists."""
    valid_agents = ["triage", "technical", "billing", "escalation"]
    return (
        payload.target_agent in valid_agents
        and bool(payload.reason)
        and bool(payload.context_summary)
        and payload.priority in ["low", "medium", "high", "critical"]
    )
