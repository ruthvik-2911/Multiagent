from backend.agents.registry import register

def run(question: str, context: dict):
    return {
        "agent": "analytics",
        "status": "failed",
        "context": "Analytics Agent not yet implemented.",
        "sources": [],
        "confidence": 0.0
    }

register("analytics", run)
