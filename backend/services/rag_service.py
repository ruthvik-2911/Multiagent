from backend.agents import supervisor

def generate_answer(question: str, session_id: str = "default") -> dict:
    return supervisor.run(question, {"session_id": session_id})
