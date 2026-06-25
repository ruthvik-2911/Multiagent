from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from docx import Document
import uuid

# ------------------------
# Qdrant Connection
# ------------------------

client = QdrantClient("localhost", port=6333)

COLLECTION_NAME = "enterprise_docs"

# ------------------------
# Create Collection
# ------------------------

collections = [c.name for c in client.get_collections().collections]

if COLLECTION_NAME not in collections:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )

# ------------------------
# Load Embedding Model
# ------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")

# ------------------------
# Read DOCX
# ------------------------

doc_path = r"data\Policies\Policy.docx"

doc = Document(doc_path)

text = "\n".join(
    [p.text for p in doc.paragraphs if p.text.strip()]
)

print("\nDocument Loaded\n")
print(text)

# ------------------------
# Generate Embedding
# ------------------------

embedding = model.encode(text).tolist()

# ------------------------
# Store in Qdrant
# ------------------------

client.upsert(
    collection_name=COLLECTION_NAME,
    points=[
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "source": "Policy.docx",
                "content": text
            }
        )
    ]
)

print("\nDocument Indexed Successfully!")
