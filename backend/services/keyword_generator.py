import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

def generate_keywords(text):
    prompt = f"""
Extract the 5 most important keywords from the following document.

Rules:
- Return ONLY comma-separated keywords.
- Do not write sentences.
- Do not number them.

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

    keywords = response.json()["response"]

    return [
        keyword.strip()
        for keyword in keywords.split(",")
    ]
