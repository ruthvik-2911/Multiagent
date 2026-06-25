from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import requests

# ------------------------
# Qdrant
# ------------------------

client = QdrantClient("localhost", port=6333)

COLLECTION_NAME = "enterprise_docs"

# ------------------------
# Embedding Model
# ------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")

# ------------------------
# Question
# ------------------------

question = input("Ask a question: ")

question_embedding = model.encode(question).tolist()

# ------------------------
# Search Qdrant
# ------------------------

results = client.query_points(
    collection_name=COLLECTION_NAME,
    query=question_embedding,
    limit=1
)

context = results.points[0].payload["content"]

# ------------------------
# Prompt
# ------------------------

prompt = f"""
Answer only from the provided context.

Context:
{context}

Question:
{question}
"""

# ------------------------
# Ollama
# ------------------------

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3.2:3b",
        "prompt": prompt,
        "stream": False
    }
)

answer = response.json()["response"]

print("\nAnswer:\n")
print(answer)
