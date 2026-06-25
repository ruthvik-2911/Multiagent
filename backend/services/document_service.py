import os

def get_all_documents() -> list[str]:
    docs = []
    for root, dirs, files in os.walk("data"):
        for file in files:
            docs.append(file)
    return docs
