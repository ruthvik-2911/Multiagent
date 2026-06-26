from backend.services.document_resolver import resolve_document

questions = [
    "Explain responsible AI usage",
    "Show me privacy rules",
    "Explain employee policy",
    "Vacation rules",
    "Sales revenue",
    "History textbook"
]

for q in questions:
    print()
    print(q)
    print(resolve_document(q))
