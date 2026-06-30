"""
email_agent.py
--------------
Agent for email questions: answer about content, summarize/triage the inbox,
and find emails by sender / subject / date.

Registered via the same registry pattern as the other agents:
    register("email", run)

Retrieval: emails are indexed in Qdrant with file_type == "eml" (set by the
Outlook connector). This agent searches across email documents only, using a
Qdrant filter on file_type, so it can answer "which emails mention X" and
"who emailed about Y" rather than locking to a single document.
"""

from backend.utils.dependencies import EMBEDDING_MODEL, QDRANT_CLIENT, COLLECTION_NAME
from qdrant_client import models
from backend.agents.registry import register


def run(question: str, context: dict) -> dict:
    # Embed the question and search ONLY email documents
    embedding = EMBEDDING_MODEL.encode(question).tolist()

    try:
        results = QDRANT_CLIENT.query_points(
            collection_name=COLLECTION_NAME,
            query=embedding,
            limit=8,
            query_filter=models.Filter(
                should=[
                    models.FieldCondition(
                        key="file_type",
                        match=models.MatchValue(value="eml"),
                    ),
                    models.FieldCondition(
                        key="source_folder",
                        match=models.MatchValue(value="emails"),
                    )
                ]
            ),
        ).points
    except Exception as e:
        return {
            "agent": "email",
            "status": "failed",
            "context": f"Email search error: {e}",
            "sources": [],
            "confidence": 0.0,
        }

    if not results:
        return {
            "agent": "email",
            "status": "failed",
            "context": "No emails matched the query.",
            "sources": [],
            "confidence": 0.0,
        }

    contexts = []
    sources = []
    for point in results:
        if point.score < 0.15:
            continue
        payload = point.payload
        contexts.append(payload.get("content", ""))
        sources.append({
            "file_name": payload.get("file_name", "Unknown"),
            "chunk_number": payload.get("chunk_number", "email"),
        })

    if not contexts:
        return {
            "agent": "email",
            "status": "failed",
            "context": "No sufficiently relevant emails found.",
            "sources": [],
            "confidence": 0.0,
        }

    return {
        "agent": "email",
        "status": "success",
        "context": "\n\n---\n\n".join(contexts),
        "sources": sources,
        "confidence": 0.85,
    }


register("email", run)
