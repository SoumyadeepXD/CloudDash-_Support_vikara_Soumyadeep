"""Triage Agent for intent classification and routing."""
import json
import structlog
from agents.base_agent import BaseAgent
from models.state import ConversationState, AgentResponse

logger = structlog.get_logger()

ROUTE_MAP = {
    "escalation_needed":  "escalation",
    "account_management": "technical",
    "general_inquiry":    "triage",
    "admin":              "triage",
    "human":              "escalation",
    "support":            "triage",
    "onboarding":         "triage",
    "technical_support":  "technical",
    "billing_support":    "billing",
    "billing_inquiry":    "billing",
    "faq":                "triage",
}

VALID_AGENTS = {"triage", "technical", "billing", "escalation"}

def _sanitize_route(route: str) -> str:
    """Map any LLM-generated route name to a valid agent name."""
    if not route:
        return "triage"
    route = route.lower().strip()
    if route in VALID_AGENTS:
        return route
    return ROUTE_MAP.get(route, "triage")

class TriageAgent(BaseAgent):
    def process(self, state: ConversationState, user_message: str) -> AgentResponse:
        prompt = self.config["system_prompt"]
        
        # Build context
        context = self._build_context_from_state(state)
        system_prompt = f"{prompt}\n\nCurrent Context:\n{context}"
        
        response_text = self._call_llm(system_prompt, user_message, state.messages)
        
        try:
            # Clean possible markdown JSON formatting
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            data = json.loads(clean_text)
            
            # Update entities
            entities_data = data.get("entities", {})
            for k, v in entities_data.items():
                if v and hasattr(state.entities, k):
                    if k == "product_refs" and isinstance(v, list):
                        state.entities.product_refs = v
                    else:
                        setattr(state.entities, k, v)
            
            # Capture secondary intent
            secondary_intent = data.get("secondary_intent", None)
            if secondary_intent:
                secondary_intent = _sanitize_route(secondary_intent)
            metadata = {"intent": data.get("intent", "general_inquiry")}
            if secondary_intent and secondary_intent in ["technical", "billing", "escalation"]:
                metadata["secondary_intent"] = secondary_intent
                    
            return AgentResponse(
                content=data.get("response", "I understand your issue, let me direct you to the right team."),
                agent=self.agent_type,
                suggested_next_agent=_sanitize_route(data.get("route_to", "triage")),
                confidence=float(data.get("confidence", 1.0)),
                metadata=metadata
            )
            
        except json.JSONDecodeError as e:
            logger.error("triage_json_parse_error", error=str(e), response=response_text[:200])
            return AgentResponse(
                content="I'm having trouble understanding. Could you please rephrase your request?",
                agent=self.agent_type,
                suggested_next_agent="triage"
            )
