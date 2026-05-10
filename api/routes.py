from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from typing import List, Dict, Any
from agents.orchestrator import Orchestrator
import json

router = APIRouter()
orchestrator = Orchestrator()

class MessageRequest(BaseModel):
    message: str

@router.post("/conversations")
async def create_conversation(response: Response):
    try:
        import uuid
        conversation_id = str(uuid.uuid4())
        state = orchestrator.get_or_create_state(conversation_id)
        response.headers["X-Trace-Id"] = state.trace_id
        return {"conversation_id": conversation_id, "trace_id": state.trace_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, req: MessageRequest, response: Response):
    try:
        if conversation_id not in orchestrator.state_store:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        state = orchestrator.state_store[conversation_id]
        response.headers["X-Trace-Id"] = state.trace_id
        
        agent_resp = orchestrator.process_message(conversation_id, req.message)
        return {
            "response": agent_resp.model_dump(),
            "state": state.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, response: Response):
    try:
        if conversation_id not in orchestrator.state_store:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        state = orchestrator.state_store[conversation_id]
        response.headers["X-Trace-Id"] = state.trace_id
        return state.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/handovers")
async def get_handovers(conversation_id: str, response: Response):
    try:
        import os
        handovers = []
        log_file = "logs/handover_audit.jsonl"
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if data.get("conversation_id") == conversation_id:
                            handovers.append(data)
                            
        if conversation_id in orchestrator.state_store:
            response.headers["X-Trace-Id"] = orchestrator.state_store[conversation_id].trace_id
            
        return handovers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    try:
        from config.settings import settings
        from retrieval.vector_store import VectorStore
        
        kb_loaded = False
        kb_chunk_count = 0
        try:
            vs = VectorStore()
            kb_chunk_count = vs.count()
            kb_loaded = kb_chunk_count > 0
        except Exception:
            pass
        
        agents_loaded = list(orchestrator.agents.keys())
        active_model = settings.gemini_model if settings.llm_provider == "gemini" else settings.ollama_model
            
        return {
            "status": "ok",
            "llm_provider": settings.llm_provider,
            "llm_model": active_model,
            "kb_loaded": kb_loaded,
            "kb_chunk_count": kb_chunk_count,
            "agents_loaded": agents_loaded
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/ingest")
def run_ingest():
    import subprocess
    result = subprocess.run(
        ["python", "knowledge_base/ingest.py"],
        capture_output=True, text=True
    )
    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
