import os
import json
import structlog
from models.state import HandoverPayload

logger = structlog.get_logger()
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
AUDIT_FILE = os.path.join(LOG_DIR, "handover_audit.jsonl")

def log_handover(payload: HandoverPayload):
    # Extract last 3 messages
    messages = payload.conversation_state.messages[-3:]
    context_snapshot = [{"role": m.role, "content": m.content} for m in messages]
    
    log_entry = {
        "timestamp": payload.timestamp.isoformat(),
        "handover_id": payload.handover_id,
        "source_agent": payload.source_agent,
        "target_agent": payload.target_agent,
        "reason": payload.reason,
        "conversation_id": payload.conversation_state.conversation_id,
        "trace_id": payload.conversation_state.trace_id,
        "priority": payload.priority,
        "context_snapshot": context_snapshot
    }
    
    logger.info("handover_executed", **log_entry)
    
    with open(AUDIT_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
