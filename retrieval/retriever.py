from models.state import RetrievedChunk, Message
from retrieval.vector_store import VectorStore
import structlog
import yaml

logger = structlog.get_logger()

class Retriever:
    def __init__(self, llm_client=None):
        self.vector_store = VectorStore()
        self.llm_client = llm_client
        
        with open("config/agents.yaml", "r") as f:
            config = yaml.safe_load(f)
            self.config = config.get("retrieval", {})

    def rewrite_query(self, history: list[Message], user_message: str) -> str:
        if not self.config.get("query_rewrite", False) or not self.llm_client:
            return user_message
            
        prompt = (
            "Rewrite this query to be keyword-rich for a technical knowledge base search.\n"
            "Focus on: product names, error types, feature names, action verbs.\n"
            "Remove: pronouns, filler words, emotional language.\n"
            "Return ONLY the rewritten query, nothing else.\n\n"
            f"Query: {user_message}"
        )
        
        try:
            if isinstance(self.llm_client, dict):
                ollama_client = self.llm_client.get("ollama")
                gemini_client = self.llm_client.get("gemini")
                
                if ollama_client:
                    try:
                        response = ollama_client.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
                        return response["message"]["content"].strip()
                    except Exception:
                        pass
                        
                if gemini_client:
                    response = gemini_client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    )
                    return response.text.strip()
            else:
                if hasattr(self.llm_client, "models"):
                    response = self.llm_client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    )
                    return response.text.strip()
                else:
                    response = self.llm_client.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
                    return response["message"]["content"].strip()
        except Exception:
            pass
            
        return user_message
        
    def retrieve(self, query: str, history: list[Message] = None) -> list[RetrievedChunk]:
        history = history or []
        search_query = self.rewrite_query(history, query)
        
        top_k = self.config.get("top_k", 5)
        results = self.vector_store.search(search_query, top_k=top_k)
        
        chunks = []
        threshold = self.config.get("score_threshold", 0.35)
        
        for res in results:
            if res["score"] < threshold:
                continue
            chunks.append(RetrievedChunk(**res))
            
        if not chunks:
            logger.warning("kb_miss", query=search_query, top_score=0.0)
            
        return chunks
