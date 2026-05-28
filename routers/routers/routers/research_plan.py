from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter(tags=["research_plan"])
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")

class PlanRequest(BaseModel):
    title: str

@router.post("/research_plan")
async def generate_plan(req: PlanRequest):
    if not DEEPSEEK_KEY:
        raise HTTPException(status_code=503, detail="مفتاح DeepSeek غير موجود")
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="الرجاء إدخال عنوان البحث")
    
    system_prompt = (
        "أنت أستاذ جامعي وخبير في منهجية البحث العلمي. مهمتك: كتابة خطة بحث شاملة ومفصلة بناءً على العنوان المقدم. "
        "يجب أن تتضمن الخطة العناصر التالية: "
        "1. مشكلة البحث (بمقدمة وصفية دقيقة). "
        "2. التساؤلات الرئيسية (3-5 أسئلة). "
        "3. أهمية البحث وأهدافه. "
        "4. فرضيات البحث (إذا أمكن). "
        "5. متغيرات البحث (مستقلة وتابعة). "
        "6. حدود البحث (مكانية وزمانية وموضوعية). "
        "7. أدوات البحث (الاستبيان، المقابلة، إلخ). "
        "8. الدراسات السابقة (إطار نظري مختصر). "
        "أخرج الخطة بشكل منظم، واضح، وباللغة العربية الفصحى، دون تعليقات إضافية."
    )
    
    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            resp = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"اكتب خطة بحث مفصلة للعنوان التالي:\n\n{req.title}"}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 4000
                }
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="فشل DeepSeek API")
            result = resp.json()
            plan = result["choices"][0]["message"]["content"].strip()
            return {"plan": plan}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
