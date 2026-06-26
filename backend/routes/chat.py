from fastapi import APIRouter
from backend.models.request_models import ChatRequest
from backend.services.rag_service import generate_answer

router = APIRouter()

@router.post("/chat")
def chat(request: ChatRequest):
    return generate_answer(request.question)
