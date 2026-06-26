import os
import uuid
from qdrant_client.models import PointStruct

from backend.utils.dependencies import EMBEDDING_MODEL, QDRANT_CLIENT, COLLECTION_NAME
from backend.utils.file_readers import read_pdf, read_docx, read_excel
from backend.utils.text_chunker import split_text
from datetime import datetime
from backend.services.metadata_generator import generate_summary
from backend.services.keyword_generator import generate_keywords
from backend.services.document_profile_service import add_profile
from backend.services.activity_service import log_activity

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
            
        file_name = os.path.basename(path)
        display_name = os.path.splitext(file_name)[0].replace("_", " ").replace("-", " ")
        
        print(f"\nReading {file_name}")
        print("Generating Summary...")
        summary = generate_summary(text)
        
        print("Generating Keywords...")
        keywords = generate_keywords(text)
        
        print("\nSummary:")
        print(summary)
        print("\nKeywords:")
        print(keywords)
        
        print("Chunking...")
        chunks = split_text(text)
        
        total_chunks = len(chunks)
        file_type = os.path.splitext(path)[1].replace(".", "")
        source_folder = os.path.basename(os.path.dirname(path))
        
        profile = {
            "file_name": file_name,
            "display_name": display_name,
            "summary": summary,
            "keywords": keywords,
            "folder": source_folder,
            "file_type": file_type,
            "total_chunks": total_chunks,
            "indexed_at": datetime.now().isoformat()
        }
        add_profile(profile)
        
        points = []
        
        for chunk_number, chunk in enumerate(chunks, start=1):
            if not chunk.strip():
                continue
                
            # ENRICH CHUNK WITH CONTEXT
            # We prepend the filename to the chunk so the embedding model knows 
            # which file this text belongs to. This fixes the issue where a chunk 
            # has "CGPA: 8.5" but doesn't explicitly mention "Ruthvik".
            chunk_text_with_context = f"File Name: {file_name}\n\n{chunk}"
            
            embedding = EMBEDDING_MODEL.encode(chunk_text_with_context).tolist()
            
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "file_name": file_name,
                        "display_name": display_name,
                        "summary": summary,
                        "keywords": keywords,
                        "file_type": file_type,
                        "chunk_number": chunk_number,
                        "total_chunks": total_chunks,
                        "source_folder": source_folder,
                        "indexed_at": datetime.now().isoformat(),
                        "content": chunk_text_with_context
                    }
                )
            )

        print("Embedding...")
        QDRANT_CLIENT.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"Uploading...\nDone. INDEXED SUCCESSFULLY: {path} ({len(chunks)} chunks)")
        log_activity("Qdrant Updated", file_name)
        log_activity("Document Indexed", file_name)

    except Exception as e:
        print(f"\nFAILED TO INDEX: {path}")
        print(e)
        log_activity("Error occurred", os.path.basename(path) if 'path' in locals() else "unknown", "Error")

def index_enterprise_document(doc):
    try:
        if not doc.content.strip():
            return
            
        file_name = doc.metadata.get("file_name", doc.title)
        display_name = doc.title
        
        print(f"\nReading {file_name} from {doc.source}")
        print("Generating Summary...")
        summary = generate_summary(doc.content)
        
        print("Generating Keywords...")
        keywords = generate_keywords(doc.content)
        
        print("Chunking...")
        chunks = split_text(doc.content)
        total_chunks = len(chunks)
        
        file_type = doc.metadata.get("file_type", "txt")
        source_folder = doc.metadata.get("folder", doc.source)
        
        profile = {
            "file_name": file_name,
            "display_name": display_name,
            "summary": summary,
            "keywords": keywords,
            "folder": source_folder,
            "file_type": file_type,
            "total_chunks": total_chunks,
            "indexed_at": datetime.now().isoformat()
        }
        add_profile(profile)
        
        points = []
        for chunk_number, chunk in enumerate(chunks, start=1):
            if not chunk.strip():
                continue
                
            chunk_text_with_context = f"File Name: {file_name}\n\n{chunk}"
            embedding = EMBEDDING_MODEL.encode(chunk_text_with_context).tolist()
            
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "file_name": file_name,
                        "display_name": display_name,
                        "summary": summary,
                        "keywords": keywords,
                        "file_type": file_type,
                        "chunk_number": chunk_number,
                        "total_chunks": total_chunks,
                        "source_folder": source_folder,
                        "indexed_at": datetime.now().isoformat(),
                        "content": chunk_text_with_context
                    }
                )
            )

        print("Embedding...")
        QDRANT_CLIENT.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"Uploading...\nDone. INDEXED SUCCESSFULLY: {file_name} ({len(chunks)} chunks)")
        log_activity("Qdrant Updated", file_name)
        log_activity(f"{doc.source.title()} Ingested", file_name)
        log_activity("Document Indexed", file_name)

    except Exception as e:
        print(f"\nFAILED TO INDEX: {doc.title}")
        print(e)
        log_activity("Error occurred", doc.title if doc else "unknown", "Error")
