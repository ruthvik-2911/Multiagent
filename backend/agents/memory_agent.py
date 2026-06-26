from backend.agents.registry import register

def run(question: str, context: dict):
    return {
        "agent": "memory",
        "status": "failed",
        "context": "Memory Agent not yet fully decoupled.",
        "sources": [],
        "confidence": 0.0
    }

register("memory", run)
