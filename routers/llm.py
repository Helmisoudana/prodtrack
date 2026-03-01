import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import List

from services.llm_service import generate, generate_stream, generate_report
from services.report_service import markdown_to_pdf

router = APIRouter(
    prefix="/chat",
    tags=["LLM Chat"]
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

@router.post("")
async def chat_endpoint(request: ChatRequest):
    try:
        messages = [msg.dict() for msg in request.messages]
        response_text = await generate(messages)
        return {"response": response_text, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest):
    messages = [msg.dict() for msg in request.messages]

    async def event_generator():
        try:
            async for chunk in generate_stream(messages):
                data = json.dumps({"text": chunk})
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            error = json.dumps({"error": str(e)})
            yield f"data: {error}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@router.post("/report")
async def chat_report_endpoint(request: ChatRequest):
    try:
        messages = [msg.dict() for msg in request.messages]
        md_content = await generate_report(messages)
        pdf_bytes = markdown_to_pdf(md_content)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=pristini_report.pdf",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
