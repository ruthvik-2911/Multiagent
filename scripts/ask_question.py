from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# ------------------------
# Connect Qdrant
# ------------------------

client = QdrantClient("localhost", port=6333)

COLLECTION_NAME = "enterprise_docs"

# ------------------------
# Load Embedding Model
# ------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")

# ------------------------
# User Question
# ------------------------

question = input("Ask a question: ")

# ------------------------
# Create Question Embedding
# ------------------------

question_embedding = model.encode(question).tolist()

# ------------------------
# Search Qdrant
# ------------------------

results = client.query_points(
    collection_name=COLLECTION_NAME,
    query=question_embedding,
    limit=1
)

print("\nMost Relevant Content:\n")

for point in results.points:
    print(point.payload["content"])
