from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter()

class ResearchRequest(BaseModel):
    query: str

@router.post("/research_iraqi")
async def search_research(payload: ResearchRequest):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key missing")
        
    # هنا يتم استدعاء سرفر البحث الأكاديمي بشكل صحيح وآمن
    return {"sources": []}
