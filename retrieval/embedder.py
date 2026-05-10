import os
from google import genai
from typing import List
from config.settings import settings

class Embedder:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = "text-embedding-004"
        
    def embed(self, text: str) -> List[float]:
        try:
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            print(f"Embedding error: {e}")
            # Fallback to zero vector if API fails (better than crashing during ingest)
            return [0.0] * 768
            
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=texts
            )
            return [e.values for e in result.embeddings]
        except Exception as e:
            print(f"Batch embedding error: {e}")
            return [[0.0] * 768 for _ in texts]
