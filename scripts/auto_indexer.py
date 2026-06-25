import os
import uuid
import time
import pandas as pd

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from pypdf import PdfReader
from docx import Document

from sentence_transformers import SentenceTransformer

from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct
)

# -----------------------------
# CONFIG
# -----------------------------

WATCH_FOLDER = "data"

COLLECTION_NAME = "enterprise_docs"

# -----------------------------
# QDRANT
# -----------------------------

client = QdrantClient(
    host="localhost",
    port=6333
)

# -----------------------------
# EMBEDDING MODEL
# -----------------------------

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# -----------------------------
# FILE READERS
# -----------------------------

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


# -----------------------------
# INDEX FILE
# -----------------------------

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

        if not text.strip():
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

        print("\nINDEXED SUCCESSFULLY")
        print(path)

    except Exception as e:

        print("\nFAILED")
        print(path)
        print(e)


# -----------------------------
# WATCHDOG
# -----------------------------

class AutoIndexer(
    FileSystemEventHandler
):

    def on_created(
        self,
        event
    ):

        if not event.is_directory:

            print(
                f"\nNEW FILE DETECTED:\n{event.src_path}"
            )

            time.sleep(2)

            index_file(
                event.src_path
            )


observer = Observer()

observer.schedule(
    AutoIndexer(),
    WATCH_FOLDER,
    recursive=True
)

observer.start()

print(
    "\nAUTO INDEXER RUNNING..."
)

try:

    while True:
        time.sleep(1)

except KeyboardInterrupt:

    observer.stop()

observer.join()
