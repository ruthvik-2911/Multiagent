from backend.utils.diagram_reader import read_diagram
import os
import uuid
from qdrant_client.models import PointStruct
from backend.utils.drawio_reader import read_drawio
from backend.utils.pdf_diagram_reader import read_pdf_diagram
from backend.utils.pdf_smart_reader import read_pdf_smart
from backend.utils.dependencies import EMBEDDING_MODEL, QDRANT_CLIENT, COLLECTION_NAME
from backend.utils.file_readers import read_pdf, read_docx, read_excel

def index_file(path):
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf":
            text = read_pdf_smart(path)
        elif ext == ".docx":
            text = read_docx(path)
        elif ext in [".xlsx", ".xls"]:
            text = read_excel(path)
        elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
            text = read_diagram(path)
        elif ext == ".drawio":
            text = read_drawio(path)
        else:
            return

        if not text.strip():
            return

        embedding = EMBEDDING_MODEL.encode(text).tolist()

        QDRANT_CLIENT.upsert(
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
        print(f"\nINDEXED SUCCESSFULLY: {path}")

    except Exception as e:
        print(f"\nFAILED TO INDEX: {path}")
        print(e)
