from backend.agents.registry import register
from backend.utils.dependencies import QDRANT_CLIENT, COLLECTION_NAME, EMBEDDING_MODEL
import pandas as pd
import requests
import re
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

def run(question: str, context: dict):
    # 1. Search Qdrant for relevant datasets
    question_embedding = EMBEDDING_MODEL.encode(question).tolist()
    
    results = QDRANT_CLIENT.query_points(
        collection_name=COLLECTION_NAME,
        query=question_embedding,
        limit=10,
    )
    
    csv_paths = []
    schemas = []
    
    for point in results.points:
        content = point.payload.get("content", "")
        paths = re.findall(r"File Path:\s*(.*?\.csv)", content)
        csv_paths.extend(paths)
        if "POWER BI" in content or "Table:" in content:
            schemas.append(content)
            
    if not csv_paths:
        return {
            "agent": "analytics",
            "status": "failed",
            "context": "I could not find any extracted tabular data (CSV) or Power BI tables relevant to your question.",
            "sources": [],
            "confidence": 0.0
        }
        
    csv_paths = list(set(csv_paths))
    
    # 2. Load the CSVs into a dictionary of DataFrames
    dataframes = {}
    loaded_info = []
    for path in csv_paths:
        try:
            df_name = f"df_{os.path.splitext(os.path.basename(path))[0].replace(' ', '_')}"
            dataframes[df_name] = pd.read_csv(path)
            columns = ", ".join(dataframes[df_name].columns.tolist())
            loaded_info.append(f"Variable `{df_name}` (Rows: {len(dataframes[df_name])}): {columns}")
        except Exception as e:
            pass

    schema_context = "\n".join(schemas)
    df_context = "\n".join(loaded_info)

    # 3. Generate Pandas code using Ollama
    prompt = f"""You are a Python Data Analyst. 
The following pandas DataFrames are already loaded in memory:
{df_context}

Question: {question}

Write Python pandas code to answer the question.
Rules:
1. DO NOT try to load the CSVs, they are already loaded into the variables listed above.
2. Store the final text answer or numerical result in a variable named `final_answer`.
3. Do not print anything. Only assign the variable `final_answer`.
4. Output ONLY valid python code. No explanations, no markdown formatting. Just the code.
"""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0}
            }
        )
        generated_code = response.json().get("response", "").strip()
        
        # Clean up markdown blocks if the model ignored the rule
        if generated_code.startswith("```"):
            generated_code = "\n".join(generated_code.split("\n")[1:-1])
            
        # 4. Execute the generated code
        exec_globals = {"pd": pd}
        exec_globals.update(dataframes)
        exec_locals = {}
        
        try:
            exec(generated_code, exec_globals, exec_locals)
            final_answer = exec_locals.get("final_answer", "Error: Variable `final_answer` was not set.")
        except Exception as e:
            final_answer = f"Error executing Python code: {str(e)}\nCode attempted:\n{generated_code}"
            
    except Exception as e:
        final_answer = f"Error generating code with Ollama: {str(e)}"
        
    final_context = f"--- ANALYTICS RESULT ---\nCode Executed:\n{generated_code}\n\nResult:\n{final_answer}"
    
    return {
        "agent": "analytics",
        "status": "success",
        "context": final_context,
        "sources": [{"file_path": p} for p in csv_paths],
        "confidence": 0.90
    }

register("analytics", run)
