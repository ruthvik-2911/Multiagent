import requests
import json
from backend.services.activity_service import log_activity

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

def create_plan(question):
    prompt = f"""
You are an Enterprise AI Planner.

Available agents:
- document (For general document queries, reading content, policy details, summaries of ONE specific document)
- graph (For finding relationships, connections, and keyword overlaps between documents)
- analytics (For financial data, sales, quantitative analysis)
- memory (For follow-up questions referencing previous conversation)
- search (For global searches across ALL documents simultaneously, e.g. "which documents have...", "find all mentions of...")

Create an execution plan by breaking the question into sub-tasks for the agents.
Return ONLY valid JSON format. Do not return any other text.

Example:
{{
 "tasks":[
   {{
      "agent":"analytics",
      "task":"Analyze sales report"
   }},
   {{
      "agent":"document",
      "task":"Summarize AI policy"
   }}
 ]
}}

Question:
{question}
"""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
        )
        text = response.json()["response"].strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        plan = json.loads(text.strip())
        if not plan.get("tasks"):
            plan["tasks"] = [{"agent": "search", "task": question}]
        log_activity("Planner Executed", question[:30] + "..." if len(question) > 30 else question)
        return plan
    except Exception as e:
        print(f"Planner error: {e}")
        return {"tasks": [{"agent": "document", "task": question}]}
