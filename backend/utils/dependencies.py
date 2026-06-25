from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

QDRANT_CLIENT = QdrantClient(
    host="localhost",
    port=6333
)

COLLECTION_NAME = "enterprise_docs"
