"""Orchestrator for managing conversation state, agents, guardrails, and handovers."""
import structlog
from typing import Dict
from models.state import ConversationState, Message, AgentResponse
from handover.protocol import create_handover
from handover.audit_log import log_handover
from guardrails.input_guard import check_input
from guardrails.output_guard import check_output
import yaml
import importlib

from config.settings import settings
from retrieval.retriever import Retriever

logger = structlog.get_logger()

VALID_AGENTS = {"triage", "technical", "billing", "escalation"}
AGENT_FALLBACK_MAP = {
    "escalation_needed":  "escalation",
    "account_management": "technical",
    "general_inquiry":    "triage",
    "admin":              "triage",
    "human":              "escalation",
    "technical_support":  "technical",
    "billing_inquiry":    "billing",
}

def _sanitize_agent(name: str) -> str:
    if not name:
        return "triage"
    name = name.lower().strip()
    if name in VALID_AGENTS:
        return name
    return AGENT_FALLBACK_MAP.get(name, "triage")

class Orchestrator:
    def __init__(self):
        self.state_store: Dict[str, ConversationState] = {}
        self.retriever = Retriever()
        
        with open("config/agents.yaml", "r") as f:
            self.config = yaml.safe_load(f)
            
        self.agents = {}
        for agent_name, agent_cfg in self.config["agents"].items():
            module_name = f"agents.{agent_name}_agent"
            class_name = "".join(word.capitalize() for word in agent_name.split("_")) + "Agent"
            try:
                module = importlib.import_module(module_name)
                agent_class = getattr(module, class_name)
                self.agents[agent_name] = agent_class(agent_name, agent_cfg, settings, self.retriever)
            except Exception as e:
                logger.error("failed_to_load_agent", agent_name=agent_name, error=str(e))
                
        if "triage" in self.agents:
            self.retriever.llm_client = self.agents["triage"].llm

    def get_or_create_state(self, conversation_id: str) -> ConversationState:
        if conversation_id not in self.state_store:
            self.state_store[conversation_id] = ConversationState(conversation_id=conversation_id)
        return self.state_store[conversation_id]

    def process_message(self, conversation_id: str, user_message: str) -> AgentResponse:
        state = self.get_or_create_state(conversation_id)
        
        logger.info("processing_started", conversation_id=conversation_id, trace_id=state.trace_id)
        
        # 1. Input Guardrails
        is_safe, reason = check_input(user_message)
        if not is_safe:
            logger.warning("input_guardrail_failed", reason=reason, conversation_id=conversation_id)
            return AgentResponse(content=f"I cannot process this request: {reason}", agent=state.current_agent)
            
        state.messages.append(Message(role="user", content=user_message))
        
        # 2. Get current agent
        agent = self.agents.get(state.current_agent) or self.agents.get("triage")
        if agent is None:
            raise RuntimeError(f"No agents loaded. Check base_agent.py for errors.")
        
        # 3. Process
        try:
            response = agent.process(state, user_message)
        except Exception as e:
            logger.error("agent_process_error", error=str(e), agent=state.current_agent)
            agent = self.agents.get("triage")
            response = agent.process(state, user_message)

        # 3.5. Capture secondary_intent from triage metadata
        if state.current_agent == "triage" and hasattr(response, 'metadata') and response.metadata:
            secondary = response.metadata.get('secondary_intent')
            if secondary and secondary in self.agents:
                state.secondary_intent = secondary
                logger.info("secondary_intent_captured", secondary_intent=secondary, conversation_id=conversation_id)
            
        # 4. Output Guardrails
        cleaned_content, warnings = check_output(response.content, response.citations)
        response.content = cleaned_content
        if warnings:
            logger.warning("output_guardrail_warnings", warnings=warnings, conversation_id=conversation_id)
            
        # 5. Check Handover
        if response.suggested_next_agent:
            response.suggested_next_agent = _sanitize_agent(response.suggested_next_agent)
            if response.suggested_next_agent not in self.agents:
                response.suggested_next_agent = None
                response.requires_handover = False

        needs_handover = response.requires_handover or (
            response.suggested_next_agent and response.suggested_next_agent != state.current_agent
        )
        
        if needs_handover and response.suggested_next_agent in self.agents:
            target_agent = response.suggested_next_agent
            logger.info("executing_handover", source=state.current_agent, target=target_agent)
            
            summary_prompt = f"""You are creating a handover summary for a customer support agent.
Summarize this conversation in 3-4 sentences covering:
1. What the customer's issue is
2. What has already been done/resolved
3. What still needs to be done
4. Key entities: customer ID, plan tier, sentiment, urgency

Be specific. Include article names cited, steps already taken, and any commitments made.
This summary goes directly to the next agent — be precise and actionable."""
            try:
                context_summary = agent._call_llm(summary_prompt, "Summarize the context.", state.messages)
            except Exception as e:
                logger.error("context_summary_failed", error=str(e))
                context_summary = "Automated summary failed."
            
            payload = create_handover(
                source_agent=state.current_agent,
                target_agent=target_agent,
                reason=response.handover_reason or "Routing to specialist",
                state=state,
                context_summary=context_summary
            )
            log_handover(payload)
            
            state.current_agent = target_agent
            new_agent = self.agents[target_agent]
            
            try:
                response = new_agent.process(state, user_message)
                cleaned_content, _ = check_output(response.content, response.citations)
                response.content = cleaned_content
            except Exception as e:
                logger.error("handover_target_error", error=str(e), agent=target_agent)
                state.current_agent = "triage"
                response = AgentResponse(content="Sorry, the specialist is unavailable. How else can I help?", agent="triage")

        # 6. Check for secondary intent handover after primary agent resolves
        if (state.secondary_intent 
            and state.current_agent != "triage" 
            and state.current_agent != state.secondary_intent
            and state.secondary_intent in self.agents
            and not state.escalated):
            
            secondary_target = state.secondary_intent
            logger.info("executing_secondary_handover", source=state.current_agent, target=secondary_target, conversation_id=conversation_id)

            secondary_summary_prompt = f"""You are creating a handover summary for a customer support agent.
The customer had two requests. The first ({state.current_agent}) has been handled.
Now summarize what the second request is about and any relevant context from the conversation.
Be specific and actionable."""
            try:
                secondary_summary = agent._call_llm(secondary_summary_prompt, "Summarize for secondary handover.", state.messages)
            except Exception:
                secondary_summary = "Secondary intent handover. See conversation history."

            secondary_payload = create_handover(
                source_agent=state.current_agent,
                target_agent=secondary_target,
                reason=f"Secondary intent handover from {state.current_agent}",
                state=state,
                context_summary=secondary_summary
            )
            log_handover(secondary_payload)
            
            state.current_agent = secondary_target
            secondary_agent = self.agents[secondary_target]
            state.secondary_intent = None  # Clear so we don't loop
            
            try:
                response = secondary_agent.process(state, user_message)
                cleaned_content, _ = check_output(response.content, response.citations)
                response.content = cleaned_content
            except Exception as e:
                logger.error("secondary_handover_error", error=str(e), agent=secondary_target)
        
        state.messages.append(Message(role="assistant", content=response.content, agent=response.agent))
        
        logger.info("processing_completed", conversation_id=conversation_id, current_agent=state.current_agent)
        
        return response
