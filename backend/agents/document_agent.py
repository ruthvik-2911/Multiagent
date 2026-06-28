from backend.services.document_profile_service import get_profile
from backend.services.profile_embedding_service import find_best_profile
from backend.services.memory_service import get_memory, set_memory
from backend.agents.registry import register
from backend.utils.dependencies import EMBEDDING_MODEL, QDRANT_CLIENT, COLLECTION_NAME
from qdrant_client.http import models

FOLLOW_UP_WORDS = [
    "it",
    "this",
    "that",
    "more",
    "continue",
    "explain more",
    "tell me more"
]

def run(question: str, context: dict) -> dict:
    session_id = context.get("session_id", "default")
    memory = get_memory(session_id)
    
    is_follow_up = False
    question_lower = question.lower()
    for word in FOLLOW_UP_WORDS:
        if word in question_lower.split() or question_lower == word or question_lower.startswith(word + " "):
            is_follow_up = True
            break
            
    if is_follow_up and memory:
        document = memory["document"]
        confidence = 1.0
        print(f"\n[Enterprise AI Resolver] Using Remembered Document: {document}")
        profile = get_profile(document)
    else:
        document, confidence = find_best_profile(question)
        
        if document and document.lower() in question.lower():
            confidence += 0.5
            print(f"\n[Enterprise AI Resolver] Exact filename match! Boosting confidence -> {confidence:.3f}")
            
        print(f"\n[Enterprise AI Resolver] Smartly Detected Target Document: {document} (Confidence: {confidence:.3f})")
        
        if confidence < 0.25:
            return {
                "agent": "document",
                "status": "failed",
                "context": "I couldn't confidently identify a relevant document.",
                "confidence": round(confidence, 3),
                "sources": []
            }
            
        profile = get_profile(document)
        
        if profile:
            set_memory(session_id, {
                "document": document,
                "summary": profile["summary"],
                "keywords": profile["keywords"]
            })
    
    qdrant_query_text = question
    llm_question = question
    if is_follow_up and profile:
        qdrant_query_text = " ".join(profile["keywords"])
        display_name = profile.get("display_name", document)
        llm_question = f"{question} regarding {display_name}"
    
    question_embedding = EMBEDDING_MODEL.encode(qdrant_query_text).tolist()

    results = QDRANT_CLIENT.query_points(
        collection_name=COLLECTION_NAME,
        query=question_embedding,
        limit=5,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="file_name",
                    match=models.MatchValue(value=document)
                )
            ]
        )
    )

    if not results.points:
        return {
            "agent": "document",
            "status": "failed",
            "context": "I couldn't find relevant context in the documents.",
            "sources": []
        }

    contexts = []
    sources = []
    
    for point in results.points:
        if point.score < 0.05:
            continue
            
        payload = point.payload
        contexts.append(payload.get("content", ""))
        
        sources.append({
            "file_name": payload.get("file_name", "Unknown"),
            "chunk_number": payload.get("chunk_number", "Unknown")
        })
        
    if not contexts:
        return {
            "agent": "document",
            "status": "failed",
            "context": "I couldn't find highly relevant information in the documents.",
            "sources": [],
            "confidence": round(confidence, 3)
        }
        
    vector_context = "\n\n".join(contexts)

    return {
        "agent": "document",
        "status": "success",
        "context": vector_context,
        "sources": sources,
        "confidence": round(confidence, 3),
        "selected_document": document,
        "summary": profile["summary"] if profile else "",
        "keywords": profile["keywords"] if profile else []
    }

register("document", run)
