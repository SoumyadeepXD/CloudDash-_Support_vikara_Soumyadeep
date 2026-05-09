import re

def check_input(message: str) -> tuple[bool, str]:
    # 1. Prompt injection patterns
    INJECTION_PATTERNS = [
        "ignore previous instructions",
        "ignore all instructions",
        "you are now",
        "pretend you are",
        "act as if",
        "forget your instructions",
        "system prompt",
        "disregard",
        "override",
        "jailbreak",
    ]
    
    msg_lower = message.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern in msg_lower:
            return False, "Prompt injection detected."
            
    # 2. Off-topic detection
    # Simple heuristic: must contain at least one relevant keyword, or be short (greetings)
    if len(msg_lower.split()) <= 5:
        return True, ""
        
    topic_keywords = [
        "cloud", "infrastructure", "aws", "gcp", "azure", "monitor", "monitoring",
        "alert", "cost", "bill", "invoice", "pay", "upgrade", "downgrade",
        "api", "key", "dashboard", "log", "metrics", "support", "help", "issue", "error", "fail", "slow",
        "account", "user", "role", "sso", "plan", "price", "refund", "charge",
        "reset", "hello", "hi", "team", "manager", "test"
    ]
    
    if not any(keyword in msg_lower for keyword in topic_keywords):
        return False, "Message appears off-topic."
        
    return True, ""
