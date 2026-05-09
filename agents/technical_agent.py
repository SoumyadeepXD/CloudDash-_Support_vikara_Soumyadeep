"""Technical Agent for RAG-based troubleshooting."""
from agents.base_agent import BaseAgent
from models.state import ConversationState, AgentResponse
import structlog

logger = structlog.get_logger()


class TechnicalAgent(BaseAgent):
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
        chunks = self.retriever.retrieve(user_message, state.messages)
        
        if not chunks:
            logger.warning("kb_miss", query=user_message, agent=self.agent_type, top_score=0.0)
            return AgentResponse(
                content="I searched our knowledge base but couldn't find specific documentation on this. I'll escalate this to our product specialist team.",
                agent=self.agent_type,
                requires_handover=True,
                suggested_next_agent="escalation",
                handover_reason="No KB chunks found for technical issue."
            )
            
        kb_context = self._format_kb_context(chunks)
        
        prompt = self.config["system_prompt"]
        system_prompt = f"{prompt}\n\n{kb_context}\n\nCURRENT ENTITIES:\n{self._build_context_from_state(state)}"
        
        response_text = self._call_llm(system_prompt, user_message, state.messages)
        
        # Ensure citations are present in the response text
        has_citation = any(f"KB-" in response_text for _ in [1])
        if not has_citation and chunks:
            # Append citations if the LLM forgot
            citation_lines = [f"[Source: {c.article_id} — {c.title}]" for c in chunks]
            response_text += "\n\n**Sources:** " + " ".join(citation_lines)
        
        suggested_agent = "technical"
        requires_handover = False
        handover_reason = None
        
        # Check for secondary intent (e.g., billing upgrade pending)
        if state.secondary_intent and state.secondary_intent in ["billing", "escalation", "technical"]:
            response_text += f"\n\nI'll now connect you with our {state.secondary_intent} team regarding your other request."
            suggested_agent = state.secondary_intent
            requires_handover = True
            handover_reason = f"Secondary intent: {state.secondary_intent} follow-up after technical resolution."
        # Detect billing-related keywords
        elif "billing" in user_message.lower() or "invoice" in user_message.lower():
            suggested_agent = "billing"
            requires_handover = True
            handover_reason = "Billing follow-up detected."
            
        return AgentResponse(
            content=response_text,
            agent=self.agent_type,
            citations=chunks,
            suggested_next_agent=suggested_agent,
            requires_handover=requires_handover,
            handover_reason=handover_reason
        )
