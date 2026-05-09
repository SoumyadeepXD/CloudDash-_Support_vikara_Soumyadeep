"""Escalation Agent for packaging handovers to human operators."""
import json
import os
from agents.base_agent import BaseAgent
from models.state import ConversationState, AgentResponse
from handover.protocol import create_handover
from handover.audit_log import log_handover
import structlog

logger = structlog.get_logger()

ESCALATION_LOG_DIR = "logs"
os.makedirs(ESCALATION_LOG_DIR, exist_ok=True)
ESCALATION_PACKAGES_FILE = os.path.join(ESCALATION_LOG_DIR, "escalation_packages.jsonl")


class EscalationAgent(BaseAgent):
    def _log_escalation_package(self, package: dict):
        with open(ESCALATION_PACKAGES_FILE, "a") as f:
            f.write(json.dumps(package) + "\n")

    def _build_operator_package(self, state, data, case_id):
        return {
            "case_id": case_id,
            "timestamp": state.updated_at.isoformat(),
            "priority": data.get("priority", "high"),
            "customer_id": state.entities.customer_id or "unknown",
            "plan": state.entities.plan or "unknown",
            "issue_summary": data.get("operator_summary", "Needs human assistance."),
            "conversation_summary": data.get("operator_summary", "See conversation."),
            "issue_tags": data.get("issue_tags", []),
            "sentiment": state.entities.sentiment or "unknown",
            "urgency": state.entities.urgency or "high",
            "recommended_first_action": data.get("recommended_action", "Review conversation and contact customer."),
            "full_conversation_turns": len(state.messages)
        }

    def _build_customer_message(self, case_id, data=None):
        if data and data.get("customer_message"):
            return data["customer_message"]
        return (
            f"I completely understand your frustration, and I want to make sure this gets resolved "
            f"for you right away. I've escalated your case to our senior support team with high "
            f"priority. A team member will reach out to you within 2-4 hours. Your case reference "
            f"number is {case_id}. Is there anything else I can note for the team before I "
            f"complete this handover?"
        )

    def process(self, state: ConversationState, user_message: str) -> AgentResponse:
        state.escalated = True
        case_id = f"CASE-{state.conversation_id[:8].upper()}"

        prompt = self.config["system_prompt"]
        system_prompt = (
            f"{prompt}\n\nCURRENT ENTITIES:\n{self._build_context_from_state(state)}"
            f"\n\nPlease respond with the JSON handover package."
        )

        response_text = self._call_llm(system_prompt, user_message, state.messages)

        try:
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            data = json.loads(clean_text.strip())
        except json.JSONDecodeError:
            data = {"priority": "high", "operator_summary": "Customer requested escalation. See conversation.", "issue_tags": [], "recommended_action": "Review conversation and contact customer."}

        pkg = self._build_operator_package(state, data, case_id)
        self._log_escalation_package(pkg)
        logger.info("escalation_package_logged", case_id=case_id, priority=pkg["priority"])

        payload = create_handover(
            source_agent=state.current_agent,
            target_agent="escalation",
            reason="Escalation requested",
            state=state,
            context_summary=data.get("operator_summary", "Needs human assistance."),
            priority=data.get("priority", "high")
        )
        log_handover(payload)

        return AgentResponse(
            content=self._build_customer_message(case_id, data),
            agent=self.agent_type,
            suggested_next_agent=None
        )
