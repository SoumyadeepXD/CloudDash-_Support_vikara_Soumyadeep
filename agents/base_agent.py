"""Base agent definition for all conversational agents."""
from abc import ABC, abstractmethod
from models.state import ConversationState, AgentResponse
from retrieval.retriever import Retriever
from config.settings import Settings
import structlog
import time

logger = structlog.get_logger()


class BaseAgent(ABC):
    def __init__(self, agent_type: str, config: dict, settings: Settings, retriever: Retriever):
        self.agent_type = agent_type
        self.config = config
        self.settings = settings
        self.retriever = retriever
        self.llm = self._init_llm()

    def _init_llm(self):
        clients = {}
        try:
            from google import genai
            clients["gemini"] = genai.Client(api_key=self.settings.gemini_api_key)
        except Exception:
            pass
            
        try:
            import ollama
            clients["ollama"] = ollama
        except Exception:
            pass
            
        return clients

    def _call_gemini(self, system_prompt: str, user_message: str, conversation_history: list) -> str:
        from google.genai import types
        full_prompt = f"{system_prompt}\n\nConversation history:\n"
        for msg in conversation_history[-6:]:
            full_prompt += f"{msg.role}: {msg.content}\n"
        full_prompt += f"\nuser: {user_message}"

        client = self.llm.get("gemini")
        if not client:
            from google import genai
            client = genai.Client(api_key=self.settings.gemini_api_key)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
            )
        )
        return response.text

    def _call_ollama(self, system_prompt: str, user_message: str, conversation_history: list) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-6:]:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_message})
        
        client = self.llm.get("ollama")
        if not client:
            import ollama
            client = ollama
            
        response = client.chat(
            model=self.settings.ollama_model,
            messages=messages
        )
        return response["message"]["content"]

    def _call_llm(self, system_prompt: str, user_message: str, conversation_history: list) -> str:
        provider = self.settings.llm_provider
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if provider == "ollama":
                    try:
                        return self._call_ollama(system_prompt, user_message, conversation_history)
                    except Exception as e:
                        error_str = str(e)
                        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                            raise  # Let outer retry handle it
                        logger.warning("ollama_call_failed", agent=self.agent_type, error=error_str, fallback="gemini")
                        return self._call_gemini(system_prompt, user_message, conversation_history)
                elif provider == "gemini":
                    try:
                        return self._call_gemini(system_prompt, user_message, conversation_history)
                    except Exception as e:
                        error_str = str(e)
                        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                            raise  # Let outer retry handle it
                        logger.warning("gemini_call_failed", agent=self.agent_type, error=error_str, fallback="ollama")
                        return self._call_ollama(system_prompt, user_message, conversation_history)
                else:
                    raise ValueError(f"Unknown LLM provider: {provider}")
            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    wait = (2 ** attempt) * 5
                    logger.warning("rate_limit_retry", attempt=attempt+1, wait_seconds=wait)
                    time.sleep(wait)
                    if attempt == max_retries - 1:
                        raise
                else:
                    logger.error("llm_call_failed", agent=self.agent_type, error=err)
                    raise

    @abstractmethod
    def process(self, state: ConversationState, user_message: str) -> AgentResponse:
        """Each agent implements its own processing logic."""
        pass

    def _build_context_from_state(self, state: ConversationState) -> str:
        """Build a context string from extracted entities for the LLM prompt."""
        e = state.entities
        parts = []
        if e.customer_id:
            parts.append(f"Customer ID: {e.customer_id}")
        if e.plan:
            parts.append(f"Plan: {e.plan}")
        if e.issue_type:
            parts.append(f"Issue: {e.issue_type}")
        if e.sentiment:
            parts.append(f"Sentiment: {e.sentiment}")
        if e.urgency:
            parts.append(f"Urgency: {e.urgency}")
        return "\n".join(parts) if parts else "No context extracted yet."
