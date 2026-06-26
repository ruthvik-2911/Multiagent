from rapidfuzz import process, fuzz
from backend.services.document_profile_service import load_profiles

def resolve_document(question: str):
    docs = load_profiles()
    
    choices = {}
    for doc in docs:
        search_text = " ".join([
            doc.get("display_name", ""),
            doc.get("summary", ""),
            " ".join(doc.get("keywords", [])),
            doc.get("folder", "")
        ])
        choices[search_text] = doc["file_name"]
    
    match = process.extractOne(
        question,
        choices.keys(),
        scorer=fuzz.partial_token_set_ratio
    )
    
    if not match:
        return None
        
    matched_key = match[0]
    score = match[1]
    filename = choices[matched_key]
    
    print("Matched:", filename)
    print("Score:", score)
    
    if score < 60:
        return None
        
    return filename
