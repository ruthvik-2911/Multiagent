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
            
    best_doc = None
    profile = None
    confidence = 0.0
    
    if is_follow_up and memory:
        best_doc = memory["document"]
        confidence = 1.0
        print(f"\n[Enterprise AI Resolver] Using Remembered Document: {best_doc}")
        profile = get_profile(best_doc)
    else:
        best_doc, confidence = find_best_profile(question)
        if best_doc and best_doc.lower() in question.lower():
            confidence += 0.5
            print(f"\n[Enterprise AI Resolver] Exact filename match! Boosting confidence -> {confidence:.3f}")
            
        print(f"\n[Enterprise AI Resolver] Best Profile Match: {best_doc} (Confidence: {confidence:.3f})")
        
        profile = get_profile(best_doc) if best_doc else None
        
        if profile and confidence >= 0.40:
            set_memory(session_id, {
                "document": best_doc,
                "summary": profile["summary"],
                "keywords": profile["keywords"]
            })
    
    # ── HYBRID GLOBAL SEARCH ──────────────────────────────────────────
    qdrant_query_text = question
    if is_follow_up and profile:
        qdrant_query_text = " ".join(profile["keywords"])
    
    question_embedding = EMBEDDING_MODEL.encode(qdrant_query_text).tolist()
    
    # A) Semantic search across ALL chunks
    semantic_results = QDRANT_CLIENT.query_points(
        collection_name=COLLECTION_NAME,
        query=question_embedding,
        limit=10,
    )
    
    # B) Document-specific chunks if confidence is high
    doc_chunks = []
    if best_doc and confidence >= 0.40:
        doc_results = QDRANT_CLIENT.query_points(
            collection_name=COLLECTION_NAME,
            query=question_embedding,
            limit=10,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="file_name",
                        match=models.MatchValue(value=best_doc)
                    )
                ]
            )
        )
        doc_chunks = doc_results.points

    # C) Keyword search across ALL chunks
    question_words = [w for w in question.lower().split() if len(w) > 2]
    keyword_results = QDRANT_CLIENT.scroll(
        collection_name=COLLECTION_NAME,
        limit=100,
        with_payload=True,
        with_vectors=False,
    )[0]
    
    keyword_chunks = []
    for point in keyword_results:
        content_lower = point.payload.get("content", "").lower()
        matches = sum(1 for w in question_words if w in content_lower)
        if matches >= 2:
            keyword_chunks.append((point, matches))
            
    keyword_chunks.sort(key=lambda x: x[1], reverse=True)
    keyword_chunks = [p for p, _ in keyword_chunks[:10]]
    
    # ── MERGE RESULTS ───────────────────────────────────────────────
    seen_ids = set()
    merged_contexts = []
    sources = []
    
    def add_chunk(point):
        pid = point.id if hasattr(point, 'id') else id(point)
        if pid in seen_ids:
            return
        seen_ids.add(pid)
        payload = point.payload
        content = payload.get("content", "")
        file_name = payload.get("file_name", "Unknown")
        if content.strip():
            merged_contexts.append(f"--- From Document: {file_name} ---\n{content}")
            sources.append({
                "file_name": file_name,
                "chunk_number": payload.get("chunk_number", "?")
            })

    # Add in priority order
    for p in doc_chunks:
        add_chunk(p)
    for p in keyword_chunks:
        add_chunk(p)
    for p in semantic_results.points:
        if p.score >= 0.15:
            add_chunk(p)
            
    merged_contexts = merged_contexts[:10]
    
    if not merged_contexts:
        return {
            "agent": "document",
            "status": "failed",
            "context": "I couldn't find relevant context in any documents.",
            "sources": [],
            "confidence": round(confidence, 3)
        }

    vector_context = "\n\n".join(merged_contexts)

    return {
        "agent": "document",
        "status": "success",
        "context": vector_context,
        "sources": sources,
        "confidence": round(confidence, 3),
        "selected_document": best_doc if confidence >= 0.40 else None,
        "summary": profile["summary"] if profile else "",
        "keywords": profile["keywords"] if profile else []
    }

register("document", run)
