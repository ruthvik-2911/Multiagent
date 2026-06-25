import requests
from backend.utils.dependencies import EMBEDDING_MODEL, QDRANT_CLIENT, COLLECTION_NAME

def generate_answer(question: str) -> str:
    question_embedding = EMBEDDING_MODEL.encode(question).tolist()

    results = QDRANT_CLIENT.query_points(
        collection_name=COLLECTION_NAME,
        query=question_embedding,
        limit=1
    )

    if not results.points:
        return "I couldn't find relevant context in the documents."

    context = results.points[0].payload["content"]

    prompt = f"""
Answer only from the provided context.

Context:
{context}

Question:
{question}
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:3b",
                "prompt": prompt,
                "stream": False
            }
        )
        answer = response.json()["response"]
        return answer
    except Exception as e:
        return f"Error contacting Ollama: {str(e)}"
