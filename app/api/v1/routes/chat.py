import json
from typing import Generator

import requests
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.base.deps import custom_generate_unique_id
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.users import UserBase
from app.config import settings

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


class ChatMessageRequest(BaseModel):
    message: str


def stream_from_external_api(message: str) -> Generator[bytes, None, None]:
    """
    Stream response from external API and yield chunks immediately.
    Returns bytes to preserve exact format from external API (SSE format).
    Uses chunk_size=1 to ensure immediate streaming without buffering.
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
    }
    
    payload = {
        'message': message
    }
    
    try:
        response = requests.post(
            settings.CHAT_API_URL,
            json=payload,
            headers=headers,
            stream=True,
            timeout=None
        )
        response.raise_for_status()
        
        # Stream chunk by chunk to ensure immediate streaming
        # Using a reasonable chunk_size (1024) to balance efficiency and immediate streaming
        # This prevents buffering and ensures status stays "pending" until streaming completes
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=False):
            if chunk:
                yield chunk
    except requests.exceptions.RequestException as e:
        # Yield error in SSE format matching SimpleDocsGPT
        error_message = f"Error: {str(e)}"
        error_data = f"data: {json.dumps({'error': error_message})}\n\n"
        yield error_data.encode('utf-8')


@router.post("/stream")
async def stream_chat(
    request: ChatMessageRequest,
    current_user: UserBase = Depends(get_current_user()),
):
    """
    Stream chat response from external API.
    Receives a message and forwards it to the external streaming API.
    Requires authentication.
    """
    return StreamingResponse(
        stream_from_external_api(request.message),
        media_type="text/event-stream",  # SSE format (SimpleDocsGPT uses text/plain but format is SSE)
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            # Optional: Add CORS headers if needed (SimpleDocsGPT includes these)
            # "Access-Control-Allow-Origin": "*",
            # "Access-Control-Allow-Methods": "POST, OPTIONS",
            # "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        }
    )

