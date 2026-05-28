from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter()

class ParaphraseRequest(BaseModel):
    text: str

@router.post("/paraphrase")
async def paraphrase_text(payload: ParaphraseRequest):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key missing")
    return {"rewritten_text": payload.text}
