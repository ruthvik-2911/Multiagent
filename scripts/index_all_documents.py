import os
import uuid
import pandas as pd

from pypdf import PdfReader
from docx import Document

from sentence_transformers import SentenceTransformer

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

# --------------------------------
# CONFIG
# --------------------------------

DATA_FOLDER = "data"

COLLECTION_NAME = "enterprise_docs"

# --------------------------------
# QDRANT
# --------------------------------

client = QdrantClient(
    host="localhost",
    port=6333
)

collections = [
    c.name
    for c in client.get_collections().collections
]

if COLLECTION_NAME not in collections:

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )

# --------------------------------
# EMBEDDING MODEL
# --------------------------------

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# --------------------------------
# HELPERS
# --------------------------------

def read_pdf(path):

    reader = PdfReader(path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def read_docx(path):

    doc = Document(path)

    text = ""

    for para in doc.paragraphs:
        text += para.text + "\n"

    return text


def read_excel(path):

    df = pd.read_excel(path)

    return df.to_string()


# --------------------------------
# INDEX FILE
# --------------------------------

def index_file(path):

    ext = os.path.splitext(path)[1].lower()

    try:

        if ext == ".pdf":
            text = read_pdf(path)

        elif ext == ".docx":
            text = read_docx(path)

        elif ext in [".xlsx", ".xls"]:
            text = read_excel(path)

        else:
            return

        if len(text.strip()) == 0:
            return

        embedding = model.encode(
            text
        ).tolist()

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "file": os.path.basename(path),
                        "content": text
                    }
                )
            ]
        )

        print(f"Indexed: {path}")

    except Exception as e:

        print(
            f"Failed: {path}"
        )

        print(e)

# --------------------------------
# SCAN ALL FILES
# --------------------------------

for root, dirs, files in os.walk(DATA_FOLDER):

    for file in files:

        path = os.path.join(
            root,
            file
        )

        index_file(path)

print("\nALL DOCUMENTS INDEXED")
