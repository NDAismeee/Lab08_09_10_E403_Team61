import os
import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="./chroma_db")
col = client.get_or_create_collection("day09_docs")
model = SentenceTransformer("all-MiniLM-L6-v2")

docs_dir = "./data/docs"

for fname in os.listdir(docs_dir):
    fpath = os.path.join(docs_dir, fname)

    if not os.path.isfile(fpath):
        continue

    try:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

    embedding = model.encode(content).tolist()

    col.upsert(
        ids=[fname],
        documents=[content],
        embeddings=[embedding],
        metadatas=[{"source": fname}]
    )

    print(f"Indexed: {fname}")

print("Index ready.")