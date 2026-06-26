import requests
from backend.utils.dependencies import EMBEDDING_MODEL, QDRANT_CLIENT, COLLECTION_NAME
from qdrant_client.models import Filter, FieldCondition, MatchValue


def generate_answer(question: str) -> str:
    """
    Answer a question from the indexed documents.

    To restrict the answer to ONE specific file, prefix the message with the
    filename and a '::' separator, e.g.:

        workflow.jpg :: describe the workflow
        SOP_ML SUMMER SCHOOL.pdf :: summarise this

    Without '::', it searches across all indexed documents as before.
    The filename must match exactly (case-sensitive, just the file name,
    not the full path).
    """
    # --- optional file scoping -------------------------------------------
    target_file = None
    if "::" in question:
        prefix, question = question.split("::", 1)
        target_file = prefix.strip()
        question = question.strip()

    query_filter = None
    if target_file:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="file",
                    match=MatchValue(value=target_file),
                )
            ]
        )

    # --- retrieve ---------------------------------------------------------
    question_embedding = EMBEDDING_MODEL.encode(question).tolist()

    results = QDRANT_CLIENT.query_points(
        collection_name=COLLECTION_NAME,
        query=question_embedding,
        query_filter=query_filter,
        limit=1,
    )

    if not results.points:
        if target_file:
            return (
                f"I couldn't find a document named '{target_file}'. "
                f"Check the exact filename (case-sensitive)."
            )
        return "I couldn't find relevant context in the documents."

    context = results.points[0].payload["content"]

    # --- generate ---------------------------------------------------------
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
                "stream": False,
                "options": {"num_ctx": 8192},
            },
        )
        answer = response.json()["response"]
        return answer
    except Exception as e:
        return f"Error contacting Ollama: {str(e)}"