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
        
    with open(PROFILE_VECTOR_FILE, "w") as f:
        json.dump(vectors, f)

def find_best_profile(question):
    with open(PROFILE_VECTOR_FILE, "r", encoding="utf-8") as f:
        vectors = json.load(f)

    question_embedding = EMBEDDING_MODEL.encode(question)

    best_score = -1
    best_document = None

    for item in vectors:
        profile_embedding = np.array(item["embedding"])

        similarity = np.dot(
            question_embedding,
            profile_embedding
        ) / (
            np.linalg.norm(question_embedding)
            *
            np.linalg.norm(profile_embedding)
        )

        if similarity > best_score:
            best_score = similarity
            best_document = item["file_name"]

    return best_document, float(best_score)
