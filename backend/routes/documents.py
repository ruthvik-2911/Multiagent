from fastapi import APIRouter
from backend.services.document_service import get_all_documents

router = APIRouter()

@router.get("/documents")
def get_documents():
    docs = get_all_documents()
    return {
        "documents": docs
    }
