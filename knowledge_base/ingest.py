import os
import sys
import json
import glob
import structlog

# Make sure we can find all modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
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
    print("Starting KB ingestion...")
    
    embedder = Embedder()
    vs = VectorStore()
    
    # At the start of ingest, always delete and recreate collection
    try:
        vs.delete_collection()
        print("Deleted existing collection")
    except Exception:
        pass  # Collection didn't exist, that's fine

    articles_dir = os.path.join(os.path.dirname(__file__), "articles")
    
    if not os.path.exists(articles_dir):
        print(f"ERROR: Articles directory not found at {articles_dir}")
        sys.exit(1)
        
    files = glob.glob(os.path.join(articles_dir, "*.json"))
    print(f"Found {len(files)} article files")
    
    if len(files) == 0:
        print("ERROR: No article JSON files found")
        sys.exit(1)
    
    total_chunks = 0
    
    for file in files:
        with open(file, "r") as f:
            article = json.load(f)
            
        print(f"Indexing article {article['id']}...")
        chunks = get_chunks(article["content"])
        
        ids = []
        embs = []
        docs = []
        metas = []
        
        for i, chunk_text in enumerate(chunks):
            doc_id = f"{article['id']}_chunk_{i}"
            
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
            
    print(f"SUCCESS: Indexed {total_chunks} chunks from {len(files)} articles")

if __name__ == "__main__":
    ingest()
    sys.exit(0)
