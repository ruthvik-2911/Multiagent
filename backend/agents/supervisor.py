from backend.agents import document_agent, graph_agent, analytics_agent, memory_agent
from backend.agents.registry import get_agent
from backend.services.planner_service import create_plan
from backend.services.response_composer import compose
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.services.activity_service import log_activity

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

def execute_task(task, context):
    agent_name = task.get("agent")
    task_query = task.get("task", "")
    print(f"[AI Supervisor] Executing task '{task_query}' via {agent_name} agent...")
    
    agent = get_agent(agent_name)
    if agent:
        log_activity("Supervisor Routed Request", agent_name)
        result = agent(task_query, context)
        log_activity("Agent Completed", f"{agent_name} agent")
        return result
    else:
        return {"agent": agent_name, "status": "failed", "context": f"Unknown agent: {agent_name}", "sources": [], "confidence": 0.0}

def run(question: str, context: dict):
    plan = create_plan(question)
    tasks = plan.get("tasks", [])
    
    print(f"\n[AI Supervisor] Generated Plan: {tasks}")
    
    results = []
    # Execute independent tasks concurrently
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(execute_task, task, context) for task in tasks]
        for future in as_completed(futures):
            results.append(future.result())
    
    final = compose(results)
    
    prompt = f"""
You are an Enterprise AI Assistant.

{final['context']}

Question:

{question}

Answer using the context provided.
If the answer cannot be found in the context, say:
"I could not find this information in the indexed documents."

Provide a clear, professional answer.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            }
        )
        answer = response.json().get("response", "")
    except Exception as e:
        answer = f"Error contacting Ollama: {str(e)}"
        
    return {
        "question": question,
        "answer": answer,
        "selected_document": next((r.get("selected_document") for r in results if r.get("selected_document")), None),
        "confidence": max([r.get("confidence", 0.0) for r in results] + [0.0]),
        "summary": next((r.get("summary") for r in results if r.get("summary")), ""),
        "keywords": next((r.get("keywords") for r in results if r.get("keywords")), []),
        "sources": final["sources"]
    }
