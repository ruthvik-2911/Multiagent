import os

DATA_FOLDER = "data"

def get_all_documents():
    documents = []
    for root, dirs, files in os.walk(DATA_FOLDER):
        for file in files:
            display_name = (
                os.path.splitext(file)[0]
                .replace("_", " ")
                .replace("-", " ")
            )
            documents.append({
                "file_name": file,
                "display_name": display_name,
                "file_type": os.path.splitext(file)[1],
                "folder": os.path.basename(root)
            })
    return documents
