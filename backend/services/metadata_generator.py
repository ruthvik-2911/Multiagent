import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

def generate_summary(text):
    prompt = f"""
You are an enterprise document analyzer.

Summarize the document in exactly 2 professional sentences.

Rules:
- Do NOT write "Here is a summary"
- Do NOT use bullet points
- Return ONLY the summary.

Document:

{text[:3000]}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]
