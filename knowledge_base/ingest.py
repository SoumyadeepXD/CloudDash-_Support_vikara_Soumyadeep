import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import json
import glob
from retrieval.vector_store import VectorStore
from retrieval.embedder import Embedder

def get_chunks(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        end = min(i + chunk_size, len(words))
        chunks.append(" ".join(words[i:end]))
        if end == len(words):
            break
        i += chunk_size - overlap
    return chunks

def ingest():
    embedder = Embedder()
    vs = VectorStore()
    
    files = glob.glob("knowledge_base/articles/*.json")
    
    total_chunks = 0
    
    for file in files:
        with open(file, "r") as f:
            article = json.load(f)
            
        chunks = get_chunks(article["content"])
        
        ids = []
        embs = []
        docs = []
        metas = []
        
        for i, chunk_text in enumerate(chunks):
            doc_id = f"{article['id']}_chunk_{i}"
            
            if vs.collection:
                existing = vs.collection.get(ids=[doc_id])
                if existing and existing["ids"] and len(existing["ids"]) > 0:
                    continue
                    
            ids.append(doc_id)
            docs.append(chunk_text)
            embs.append(embedder.embed(chunk_text))
            metas.append({
                "article_id": article["id"],
                "title": article["title"],
                "category": article["category"],
                "tags": ",".join(article.get("tags", [])),
                "applies_to": ",".join(article.get("applies_to", []))
            })
            total_chunks += 1
            
        if ids:
            vs.add_documents(ids=ids, embeddings=embs, documents=docs, metadatas=metas)
            
    print(f"Indexed {total_chunks} chunks from {len(files)} articles")

if __name__ == "__main__":
    ingest()
