from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter()

class PlanRequest(BaseModel):
    title: str

@router.post("/research_plan")
async def generate_plan(payload: PlanRequest):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key missing")
    return {"plan": f"خطة بحث مقترحة لعنوان: {payload.title}"}
