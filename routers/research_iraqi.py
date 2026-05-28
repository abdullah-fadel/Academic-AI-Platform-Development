from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import re
import os

router = APIRouter(tags=["research_iraqi"])

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")

class SearchRequest(BaseModel):
    query: str

@router.post("/research_iraqi")
async def iraqi_researcher(req: SearchRequest):
    """
    يبحث في Semantic Scholar عن أحدث 20 مصدراً (2021-2025)
    ويعزز البحث باستخدام DeepSeek لتحسين الاستعلام إن أمكن.
    """
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="الرجاء إدخال عنوان البحث")
    
    # تحسين الاستعلام عبر DeepSeek (اختياري)
    enhanced_query = query
    if DEEPSEEK_KEY:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "أنت مساعد بحثي. قم بتحويل سؤال المستخدم إلى استعلام بحث قصير وفعال باللغة الإنجليزية أو العربية."},
                            {"role": "user", "content": f"حول هذا النص إلى استعلام بحث قصير: {query}"}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 50
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    enhanced_query = data["choices"][0]["message"]["content"].strip()
        except:
            pass  # استخدم الاستعلام الأصلي
    
    # البحث في Semantic Scholar
    sources = []
    async with httpx.AsyncClient(timeout=25.0) as client:
        try:
            response = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": enhanced_query,
                    "limit": 20,
                    "fields": "title,authors,year,url,openAccessPdf,abstract,venue,publicationDate"
                }
            )
            if response.status_code == 200:
                data = response.json()
                for paper in data.get("data", []):
                    year = paper.get("year")
                    # تصفية السنوات 2021-2025
                    if year and 2021 <= int(year) <= 2025:
                        pdf_info = paper.get("openAccessPdf")
                        pdf_url = pdf_info.get("url") if pdf_info else None
                        authors_list = paper.get("authors", [])
                        authors_names = [a.get("name") for a in authors_list[:3] if a.get("name")]
                        sources.append({
                            "title": paper.get("title", "بدون عنوان"),
                            "authors": ", ".join(authors_names) if authors_names else "مؤلف غير محدد",
                            "year": year,
                            "journal": paper.get("venue") or "مجلة علمية",
                            "abstract": (paper.get("abstract") or "")[:250],
                            "url": paper.get("url"),
                            "pdf_url": pdf_url
                        })
                        if len(sources) >= 20:
                            break
        except Exception as e:
            print("خطأ في Semantic Scholar:", e)
            raise HTTPException(status_code=500, detail="فشل في جلب المصادر")
    
    if not sources:
        return {"sources": [], "message": "لم يتم العثور على مصادر حديثة (2021-2025). حاول تغيير كلمات البحث."}
    return {"sources": sources}
