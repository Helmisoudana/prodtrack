# routers/llm.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from services.llm_service import generate

# Export 'router' not 'chat_bp'
router = APIRouter(
    prefix="/api/chat",
    tags=["LLM Chat"]
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    try:
        messages = [msg.dict() for msg in request.messages]
        response_text = await generate(messages)
        return {"response": response_text, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))