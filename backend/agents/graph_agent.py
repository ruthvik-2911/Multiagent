from backend.services.graph_service import search_keywords
from backend.agents.registry import register

def run(question: str, context: dict):
    graph_results = search_keywords(question)
    graph_context = ""
    sources = []
    for item in graph_results:
        graph_context += f"Document: {item['file']}\nKeywords: {', '.join(item['keywords'])}\n\n"
        sources.append({"file_name": item["file"], "chunk_number": "graph"})
        
    return {
        "agent": "graph",
        "status": "success" if graph_context else "failed",
        "context": graph_context,
        "sources": sources,
        "confidence": 0.9 if graph_context else 0.0
    }

register("graph", run)
