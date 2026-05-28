from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter(tags=["paraphrase"])
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")

class ParaphraseRequest(BaseModel):
    text: str

@router.post("/paraphrase")
async def paraphrase_text(req: ParaphraseRequest):
    if not DEEPSEEK_KEY:
        raise HTTPException(status_code=503, detail="مفتاح DeepSeek غير موجود")
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="النص فارغ")
    
    system_prompt = (
        "أنت خبير أكاديمي متخصص في إعادة صياغة النصوص بطريقة بشرية، طبيعية، ورصينة. "
        "مهمتك: إعادة صياغة النص المقدم بالكامل مع الحفاظ على المعنى الأصلي وجميع المعلومات (أسماء، تواريخ، استشهادات). "
        "استخدم أسلوباً أكاديمياً محكماً، وتجنب الركاكة، ولا تزد الطول كثيراً. "
        "أخرج النص النهائي فقط بدون أي مقدمات أو تعليقات."
    )
    
    async with httpx.AsyncClient(timeout=70.0) as client:
        try:
            resp = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"أعد صياغة النص التالي:\n\n{req.text}"}
                    ],
                    "temperature": 0.6,
                    "max_tokens": 4000
                }
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="فشل DeepSeek API")
            result = resp.json()
            rewritten = result["choices"][0]["message"]["content"].strip()
            return {"rewritten_text": rewritten}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
