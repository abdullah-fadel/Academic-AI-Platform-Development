from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from routers.research_iraqi import router as research_iraqi_router
from routers.paraphrase import router as paraphrase_router
from routers.research_plan import router as plan_router
from routers.admin import router as admin_router
from models import SessionLocal, Article, Visit
from datetime import datetime
import os

app = FastAPI(title="مكتبة الإنجاز")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# تضمين الرواتر
app.include_router(research_iraqi_router, prefix="/api")
app.include_router(paraphrase_router, prefix="/api")
app.include_router(plan_router, prefix="/api")
app.include_router(admin_router, prefix="/admin")

# تسجيل الزيارات
@app.middleware("http")
async def track_visits(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    path = request.url.path
    db = SessionLocal()
    visit = Visit(ip=client_ip, user_agent=user_agent, path=path)
    db.add(visit)
    db.commit()
    db.close()
    return await call_next(request)

# الصفحة الرئيسية
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    db = SessionLocal()
    articles = db.query(Article).order_by(Article.created_at.desc()).all()
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_visits = db.query(Visit).filter(Visit.visited_at >= today_start).count()
    total_visits = db.query(Visit).count()
    db.close()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>مكتبة الإنجاز | منصة أكاديمية ذكية</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');
            * {{ font-family: 'Cairo', sans-serif; }}
            .gradient-bg {{ background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%); }}
            .card-hover:hover {{ transform: translateY(-4px); transition: all 0.3s ease; }}
        </style>
    </head>
    <body class="bg-gray-50">
        <nav class="bg-white/80 backdrop-blur-md sticky top-0 z-50 shadow-sm border-b">
            <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
                <div class="flex items-center gap-2">
                    <i class="fa-solid fa-landmark text-indigo-700 text-2xl"></i>
                    <span class="text-xl font-bold text-indigo-900">مكتبة الإنجاز</span>
                </div>
                <div class="hidden md:flex gap-6 font-semibold">
                    <a href="/" class="hover:text-indigo-600">الرئيسية</a>
                    <a href="/tools/research" class="hover:text-indigo-600">🔍 الباحث العراقي</a>
                    <a href="/tools/paraphrase" class="hover:text-indigo-600">✍️ إعادة الصياغة</a>
                    <a href="/tools/plan" class="hover:text-indigo-600">📝 خطة البحث</a>
                    <a href="/admin/dashboard" class="bg-gray-100 px-3 py-1 rounded-full text-sm">👑 الأدمن</a>
                </div>
            </div>
        </nav>
        <div class="max-w-7xl mx-auto px-4 py-8">
            <div class="gradient-bg rounded-2xl text-white p-10 text-center mb-12">
                <h1 class="text-4xl font-black">الذكاء الاصطناعي للبحث الأكاديمي</h1>
                <p class="text-lg mt-4 opacity-90">استخرج المصادر، أعد صياغة النصوص، واكتب خطة بحثك بكل احترافية.</p>
                <div class="flex justify-center gap-6 mt-6 text-sm">
                    <span class="bg-white/20 px-4 py-2 rounded-full">📊 زوار اليوم: {today_visits}</span>
                    <span class="bg-white/20 px-4 py-2 rounded-full">👥 إجمالي الزوار: {total_visits}</span>
                </div>
            </div>
            <div class="grid md:grid-cols-3 gap-8 mb-16">
                <div class="bg-white p-6 rounded-2xl shadow card-hover text-center">
                    <i class="fa-solid fa-magnifying-glass-chart text-4xl text-indigo-600 mb-3"></i>
                    <h3 class="text-xl font-bold">الباحث العراقي</h3>
                    <p class="text-gray-500 mt-2">أحدث المصادر العلمية (2021-2025) مع روابط PDF</p>
                    <a href="/tools/research" class="mt-4 inline-block text-indigo-600 font-bold">جرب الآن →</a>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow card-hover text-center">
                    <i class="fa-solid fa-pen-fancy text-4xl text-emerald-600 mb-3"></i>
                    <h3 class="text-xl font-bold">إعادة الصياغة</h3>
                    <p class="text-gray-500 mt-2">صياغة بشرية أكاديمية لتجنب الاستلال</p>
                    <a href="/tools/paraphrase" class="mt-4 inline-block text-emerald-600 font-bold">جرب الآن →</a>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow card-hover text-center">
                    <i class="fa-solid fa-diagram-project text-4xl text-amber-600 mb-3"></i>
                    <h3 class="text-xl font-bold">خطة البحث</h3>
                    <p class="text-gray-500 mt-2">منهجية متكاملة حسب عنوان بحثك</p>
                    <a href="/tools/plan" class="mt-4 inline-block text-amber-600 font-bold">جرب الآن →</a>
                </div>
            </div>
            <div>
                <h2 class="text-2xl font-bold border-r-4 border-indigo-600 pr-3 mb-6">📖 أحدث المقالات</h2>
                <div class="grid md:grid-cols-2 gap-6">
    """
    for art in articles:
        html += f"""
        <div class="bg-white p-5 rounded-xl shadow-sm border">
            <h3 class="font-bold text-lg">{art.title}</h3>
            <p class="text-gray-500 text-sm mt-1">{art.content[:120]}...</p>
            <small class="text-gray-400">{art.created_at.strftime('%Y-%m-%d')}</small>
        </div>
        """
    html += """
                </div>
            </div>
        </div>
        <footer class="bg-white border-t py-6 text-center text-gray-500 text-sm mt-12">© 2025 مكتبة الإنجاز</footer>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# صفحات الأدوات (مختصرة، لكنها كاملة في ملفات منفصلة – يمكنك استخدام نفس الروابط)
@app.get("/tools/research", response_class=HTMLResponse)
async def tool_research():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html dir="rtl">
    <head><meta charset="UTF-8"><title>الباحث العراقي</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="p-6"><a href="/">← الرئيسية</a>
    <div class="bg-white p-6 rounded shadow"><input id="q" class="border p-2 w-full"><button onclick="search()" class="bg-indigo-600 text-white p-2 mt-2">بحث</button><div id="res"></div></div>
    <script>async function search(){let q=document.getElementById('q').value;let r=await fetch('/api/research_iraqi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q})});let d=await r.json();let html='';d.sources.forEach(s=>{html+=`<div><b>${s.title}</b><br>${s.authors} (${s.year})<br><a href='${s.pdf_url||s.url}' target='_blank'>PDF</a></div>`;});document.getElementById('res').innerHTML=html;}</script></body></html>
    """)

@app.get("/tools/paraphrase", response_class=HTMLResponse)
async def tool_paraphrase():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html dir="rtl"><head><meta charset="UTF-8"><title>إعادة الصياغة</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="p-6"><a href="/">← الرئيسية</a><div class="bg-white p-6 rounded"><textarea id="txt" rows="6" class="border w-full"></textarea><button onclick="para()" class="bg-indigo-600 text-white p-2 mt-2">صياغة</button><div id="out" class="mt-4"></div></div>
    <script>async function para(){let t=document.getElementById('txt').value;let r=await fetch('/api/paraphrase',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});let d=await r.json();document.getElementById('out').innerHTML=d.rewritten_text;}</script></body></html>
    """)

@app.get("/tools/plan", response_class=HTMLResponse)
async def tool_plan():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html dir="rtl"><head><meta charset="UTF-8"><title>خطة البحث</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="p-6"><a href="/">← الرئيسية</a><div class="bg-white p-6 rounded"><input id="title" class="border p-2 w-full" placeholder="عنوان البحث"><button onclick="gen()" class="bg-indigo-600 text-white p-2 mt-2">إنشاء خطة</button><div id="out" class="mt-4 whitespace-pre-wrap"></div></div>
    <script>async function gen(){let t=document.getElementById('title').value;let r=await fetch('/api/research_plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:t})});let d=await r.json();document.getElementById('out').innerHTML=d.plan;}</script></body></html>
    """)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
