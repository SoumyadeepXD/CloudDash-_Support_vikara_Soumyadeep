import os
os.environ["CHROMA_TELEMETRY"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "false"
import chromadb
from chromadb.config import Settings
from retrieval.embedder import Embedder

class VectorStore:
    def __init__(self):
        import chromadb
        chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.client = chromadb.PersistentClient(path=chroma_dir)
        self.collection_name = "clouddash_kb"
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
        except Exception:
            # Collection doesn't exist yet — will be created during ingest
            self.collection = None
        self.embedder = Embedder()

        
    def add_documents(self, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]):
        if self.collection is None:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
    def search(self, query: str, top_k: int = 5):
        if self.collection is None:
            return []
        embedding = self.embedder.embed(query)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )
        
        if not results or not results["documents"] or not results["documents"][0]:
            return []
            
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [0.0]*len(docs)
        
        out = []
        for d, m, dist in zip(docs, metas, distances):
            score = 1.0 - dist
            out.append({
                "article_id": m.get("article_id", "unknown"),
                "title": m.get("title", "unknown"),
                "category": m.get("category", "unknown"),
                "content": d,
                "score": score
            })
        return out
        
    def delete_collection(self):
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = None
        except Exception:
            pass

    def count(self) -> int:
        if self.collection is None:
            return 0
        return self.collection.count()
