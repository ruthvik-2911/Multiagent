from backend.services.profile_embedding_service import find_best_profile

questions = [
    "Explain responsible AI usage",
    "Employee privacy",
    "Sales revenue",
    "History textbook",
    "Resume of Ruthvik"
]

for q in questions:
    doc, score = find_best_profile(q)
    print()
    print(q)
    print(doc)
    print(score)
