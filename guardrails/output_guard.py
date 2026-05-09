import re
from models.state import RetrievedChunk

EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_PATTERN = re.compile(r'\b\d{10,}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b')
CARD_PATTERN  = re.compile(r'\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b')

def check_output(response: str, retrieved_chunks: list[RetrievedChunk]) -> tuple[str, list[str]]:
    warnings = []
    
    # 1. PII Redaction
    cleaned = EMAIL_PATTERN.sub('[REDACTED]', response)
    cleaned = PHONE_PATTERN.sub('[REDACTED]', cleaned)
    cleaned = CARD_PATTERN.sub('[REDACTED]', cleaned)
    
    # 2. Hallucination check
    kb_content = " ".join([chunk.content for chunk in retrieved_chunks]).lower()
    
    # Check for specific prices not in KB
    prices = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', cleaned)
    hallucinated_price = False
    for price in prices:
        if price not in kb_content:
            hallucinated_price = True
            break
            
    # Simple check for plan names not in KB
    plans = ["starter", "pro", "enterprise"]
    hallucinated_plan = False
    for plan in plans:
        if plan in cleaned.lower() and plan not in kb_content:
            hallucinated_plan = True
            break
            
    if hallucinated_price or hallucinated_plan:
        cleaned += "\n\nNote: Some details may require verification with our team."
        
    # 3. Policy violation
    policy_keywords = ["guarantee", "100% refund", "full refund"]
    for word in policy_keywords:
        if word in cleaned.lower() and word not in kb_content:
            warnings.append(f"Policy violation warning: mentions '{word}' without KB backing.")
            
    return cleaned, warnings
