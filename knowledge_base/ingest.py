import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

    # Use absolute path so it works both locally and on Railway
    base_dir = os.path.dirname(os.path.abspath(__file__))
    files = glob.glob(os.path.join(base_dir, "articles", "*.json"))

    print(f"Found {len(files)} article files")

    if len(files) == 0:
        print("ERROR: No articles found")
        sys.exit(1)

    # Always delete and recreate collection for clean ingest
    try:
        vs.client.delete_collection("clouddash_kb")
        print("Deleted existing collection")
    except Exception:
        pass

    vs.collection = vs.client.create_collection(
        name="clouddash_kb",
        metadata={"hnsw:space": "cosine"}
    )
    print("Created fresh collection")

    total_chunks = 0

    for file in files:
        with open(file, "r") as f:
            article = json.load(f)

        chunks = get_chunks(article["content"])

        ids, embs, docs, metas = [], [], [], []

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
            print(f"Indexed {article['id']} — {len(ids)} chunks")

    print(f"SUCCESS: Indexed {total_chunks} chunks from {len(files)} articles")

if __name__ == "__main__":
    ingest()
