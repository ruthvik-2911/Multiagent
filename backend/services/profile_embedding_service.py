import json
import os
import numpy as np
from backend.utils.dependencies import EMBEDDING_MODEL
from backend.services.document_profile_service import load_profiles

PROFILE_VECTOR_FILE = "backend/storage/profile_embeddings.json"

def build_profile_embeddings():
    profiles = load_profiles()
    vectors = []
    
    for profile in profiles:
        text = " ".join([
            profile.get("display_name", ""),
            profile.get("summary", ""),
            " ".join(profile.get("keywords", []))
        ])
        
        embedding = EMBEDDING_MODEL.encode(text).tolist()
        
        vectors.append({
            "file_name": profile["file_name"],
            "embedding": embedding
        })
        
    os.makedirs(os.path.dirname(PROFILE_VECTOR_FILE), exist_ok=True)
    with open(PROFILE_VECTOR_FILE, "w") as f:
        json.dump(vectors, f)

def find_best_profile(question):
    if not os.path.exists(PROFILE_VECTOR_FILE):
        return None, 0.0
        
    with open(PROFILE_VECTOR_FILE, "r", encoding="utf-8") as f:
        vectors = json.load(f)

    if not vectors:
        return None, 0.0

    question_embedding = EMBEDDING_MODEL.encode(question)
    question_lower = question.lower()

    best_score = -1
    best_document = None

    for item in vectors:
        file_name = item["file_name"]
        profile_embedding = np.array(item["embedding"])

        similarity = np.dot(
            question_embedding,
            profile_embedding
        ) / (
            np.linalg.norm(question_embedding)
            *
            np.linalg.norm(profile_embedding)
        )
        
        # Boost for exact filename or keyword matches in the query
        if file_name.lower() in question_lower:
            similarity += 0.3
            
        # Optional: check if "email" is in question, slightly boost email profiles, etc.
        if "email" in question_lower and "eml" in file_name.lower():
            similarity += 0.1

        if similarity > best_score:
            best_score = similarity
            best_document = file_name

    return best_document, float(best_score)
