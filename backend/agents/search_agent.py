from backend.agents.registry import register
from backend.utils.dependencies import EMBEDDING_MODEL, QDRANT_CLIENT, COLLECTION_NAME

def run(question: str, context: dict) -> dict:
    print(f"\n[Global Search Agent] Searching across ALL documents for: {question}")
    question_embedding = EMBEDDING_MODEL.encode(question).tolist()
    
    results = QDRANT_CLIENT.query_points(
        collection_name=COLLECTION_NAME,
        query=question_embedding,
        limit=10,
    )
    
    if not results.points:
        return {
            "agent": "search",
            "status": "failed",
            "context": "I couldn't find any relevant documents across the database.",
            "sources": [],
            "confidence": 0.0
        }
        
    contexts = []
    sources = []
    
    for point in results.points:
        if point.score < 0.15:
            continue
            
        payload = point.payload
        file_name = payload.get("file_name", "Unknown Document")
        content = payload.get("content", "")
        contexts.append(f"--- From Document: {file_name} ---\n{content}")
        
        sources.append({
            "file_name": file_name,
            "chunk_number": payload.get("chunk_number", "Unknown")
        })
        
    if not contexts:
        return {
            "agent": "search",
            "status": "failed",
            "context": "I couldn't find highly relevant information.",
            "sources": [],
            "confidence": 0.0
        }
        
    vector_context = "\n\n".join(contexts)
    
    return {
        "agent": "search",
        "status": "success",
        "context": vector_context,
        "sources": sources,
        "confidence": 0.8,
        "selected_document": None,
        "summary": "",
        "keywords": []
    }

register("search", run)
