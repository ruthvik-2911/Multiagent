import os
import sys

# Ensure backend can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.indexer import index_file
from backend.utils.dependencies import QDRANT_CLIENT, COLLECTION_NAME
from qdrant_client.models import Distance, VectorParams
import json
from backend.services.graph_service import run_query
from backend.services.document_profile_service import PROFILE_FILE
from backend.services.profile_embedding_service import PROFILE_VECTOR_FILE

DATA_FOLDER = "data"

# Ensure collection exists or recreate it cleanly
collections = [c.name for c in QDRANT_CLIENT.get_collections().collections]
if COLLECTION_NAME in collections:
    QDRANT_CLIENT.delete_collection(COLLECTION_NAME)

QDRANT_CLIENT.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

print("Wiping Neo4j Graph...")
run_query("MATCH (n) DETACH DELETE n")

print("Wiping JSON Profiles...")
with open(PROFILE_FILE, "w", encoding="utf-8") as f:
    json.dump([], f)
    
with open(PROFILE_VECTOR_FILE, "w", encoding="utf-8") as f:
    json.dump([], f)

folders = ["data", "emails", "sharepoint", "powerbi", "onedrive", "contracts"]
for folder in folders:
    if os.path.exists(folder):
        for root, dirs, files in os.walk(folder):
            for file in files:
                path = os.path.join(root, file)
                index_file(path)

print("\nALL DOCUMENTS INDEXED")
