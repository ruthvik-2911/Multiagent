import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

def choose_agent(question):
    prompt = f"""
You are an AI Router.

Available agents:
1. document - For answering general questions, explaining policies, reading resumes, history, and summarizing document contents.
2. graph - For finding relationships between documents, or discovering which documents share keywords.
3. analytics - For quantitative queries, financial data, sales, numbers, or revenue.
4. memory - For generic follow-up questions that reference previous context (e.g., "tell me more", "explain further", "what about it?").

Return ONLY valid JSON format. Do not return any other text.

Example:
{{"agent": "document", "confidence": 0.96}}

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
        text = response.json()["response"]
        return json.loads(text.strip())
    except Exception as e:
        print(f"Router error: {e}")
        return {"agent": "document", "confidence": 0.0}
