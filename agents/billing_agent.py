"""Billing Agent for RAG-based billing and account lookup."""
from agents.base_agent import BaseAgent
from models.state import ConversationState, AgentResponse
import re
import structlog

logger = structlog.get_logger()

ESCALATION_TRIGGERS = [
    "manager", "supervisor", "speak to a human", "speak to someone",
    "charged twice", "double charged", "duplicate charge",
    "refund", "lawsuit", "fraud", "unacceptable"
]


class BillingAgent(BaseAgent):
    def mock_account_lookup(self, customer_id: str) -> dict:
        return {
            "plan": "Pro",
            "billing_date": "2026-05-01",
            "amount_due": "$199.00",
            "last_invoice": "Paid",
            "customer_id": customer_id
        }

    def _should_escalate(self, message: str) -> bool:
        message_lower = message.lower()
        return any(trigger in message_lower for trigger in ESCALATION_TRIGGERS)

    def _format_kb_context(self, chunks) -> str:
        """Format retrieved chunks into structured context for the LLM prompt."""
        if not chunks:
            return "--- RETRIEVED KNOWLEDGE BASE ARTICLES ---\nNo relevant articles found.\n--- END OF RETRIEVED ARTICLES ---"
        
        parts = ["--- RETRIEVED KNOWLEDGE BASE ARTICLES ---"]
        for idx, chunk in enumerate(chunks, 1):
            parts.append(
                f"[{idx}] {chunk.article_id}: {chunk.title} (score: {chunk.score:.2f})\n"
                f"Content: {chunk.content}"
            )
        parts.append("--- END OF RETRIEVED ARTICLES ---")
        parts.append("\nUse ONLY the above articles to answer. Cite each one you use as [Source: KB-XXX — Title].")
        parts.append("If the articles don't contain the answer, say so explicitly.")
        return "\n\n".join(parts)

    def process(self, state: ConversationState, user_message: str) -> AgentResponse:
        msg_lower = user_message.lower()
        force_escalate = self._should_escalate(user_message)
        
        if force_escalate:
            logger.info("billing_auto_escalation_triggered", agent=self.agent_type, message_preview=msg_lower[:80])

        chunks = self.retriever.retrieve(user_message, state.messages)
        billing_chunks = [c for c in chunks if "Billing" in c.category or "Pricing" in c.category]
        if not billing_chunks:
            billing_chunks = chunks  # Fall back
            
        kb_context = self._format_kb_context(billing_chunks)
        
        account_data = ""
        if state.entities.customer_id:
            acc = self.mock_account_lookup(state.entities.customer_id)
            account_data = f"Account Info:\nPlan: {acc['plan']}\nAmount Due: {acc['amount_due']}\nLast Invoice: {acc['last_invoice']}"
            
        prompt = self.config["system_prompt"]
        system_prompt = f"{prompt}\n\n{kb_context}\n\nACCOUNT DATA:\n{account_data}\n\nCURRENT ENTITIES:\n{self._build_context_from_state(state)}"
        
        response_text = self._call_llm(system_prompt, user_message, state.messages)
        
        if force_escalate:
            return AgentResponse(
                content=response_text,
                agent=self.agent_type,
                citations=billing_chunks,
                requires_handover=True,
                suggested_next_agent="escalation",
                handover_reason="Customer requested human agent / high-urgency billing issue"
            )
        
        return AgentResponse(
            content=response_text,
            agent=self.agent_type,
            citations=billing_chunks,
            suggested_next_agent="billing"
        )
