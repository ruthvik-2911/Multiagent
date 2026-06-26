from backend.services.document_catalog import get_all_documents

docs = get_all_documents()

for doc in docs:
    print(doc)
