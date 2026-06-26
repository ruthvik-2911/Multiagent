import os
import sys

# Ensure backend can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.indexer import index_file
from backend.utils.dependencies import QDRANT_CLIENT, COLLECTION_NAME
from qdrant_client.models import Distance, VectorParams

DATA_FOLDER = "data"

# Ensure collection exists or recreate it cleanly
collections = [c.name for c in QDRANT_CLIENT.get_collections().collections]
if COLLECTION_NAME in collections:
    QDRANT_CLIENT.delete_collection(COLLECTION_NAME)

QDRANT_CLIENT.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

for root, dirs, files in os.walk(DATA_FOLDER):
    for file in files:
        path = os.path.join(root, file)
        index_file(path)

print("\nALL DOCUMENTS INDEXED")
