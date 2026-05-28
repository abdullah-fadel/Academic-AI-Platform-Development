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

app = FastAPI(title="منصة الإنجاز")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# تضمين الراوترات بالأسماء المستوردة الصحيحة والمطابقة 100%
app.include_router(research_iraqi_router, prefix="/api")
app.include_router(paraphrase_router, prefix="/api")
app.include_router(plan_router, prefix="/api")
app.include_router(admin_router, prefix="/admin")

# تسجيل الزيارات بطريقة آمنة تمنع قفل قاعدة البيانات (Database Locks)
@app.middleware("http")
async def track_visits(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    path = request.url.path
    
    db = SessionLocal()
    try:
        visit = Visit(ip=client_ip, user_agent=user_agent, path=path)
        db.add(visit)
        db.commit()
    except Exception:
        pass  # تخطي أي خطأ في تسجيل الزيارة لكي لا يتوقف الموقع عن العمل
    finally:
        db.close()  # الإغلاق مضمون هنا حتى لو فشل الـ commit
        
    return await call_next(request)

# ------------------- الصفحة الرئيسية -------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    db = SessionLocal()
    try:
        articles = db.query(Article).order_by(Article.created_at.desc()).all()
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_visits = db.query(Visit).filter(Visit.visited_at >= today_start).count()
        total_visits = db.query(Visit).count()
    finally:
        db.close()
        
    html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>منصة الإنجاز الأكاديمية</title>
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
                    <span class="text-xl font-bold text-indigo-900">منصة الإنجاز</span>
                </div>
                <div class="hidden md:flex gap-6 font-semibold">
                    <a href="/" class="hover:text-indigo-600">الرئيسية</a>
                    <a href="/tools/research" class="hover:text-indigo-600">🔍 الباحث الأكاديمي</a>
                    <a href="/tools/paraphrase" class="hover:text-indigo-600">✍️ إعادة الصياغة</a>
                    <a href="/tools/plan" class="hover:text-indigo-600">📝 خطة البحث</a>
                    <a href="/admin/dashboard" class="bg-gray-100 px-3 py-1 rounded-full text-sm">👑 الأدمن</a>
                </div>
            </div>
        </nav>
        <div class="max-w-7xl mx-auto px-4 py-8">
            <div class="gradient-bg rounded-2xl text-white p-10 text-center mb-12">
                <h1 class="text-4xl font-black">الخدمات والأدوات البحثية المتقدمة</h1>
                <p class="text-lg mt-4 opacity-90">استخرج المصادر، أعد صياغة النصوص، واكتب خطة بحثك بكل احترافية.</p>
                <div class="flex justify-center gap-6 mt-6 text-sm">
                    <span class="bg-white/20 px-4 py-2 rounded-full">📊 زوار اليوم: {today_visits}</span>
                    <span class="bg-white/20 px-4 py-2 rounded-full">👥 إجمالي الزوار: {total_visits}</span>
                </div>
            </div>
            <div class="grid md:grid-cols-3 gap-8 mb-16">
                <div class="bg-white p-6 rounded-2xl shadow card-hover text-center">
                    <i class="fa-solid fa-magnifying-glass-chart text-4xl text-indigo-600 mb-3"></i>
                    <h3 class="text-xl font-bold">الباحث الأكاديمي</h3>
                    <p class="text-gray-500 mt-2">أحدث المصادر العلمية الحديثة مع روابط PDF مباشرة</p>
                    <a href="/tools/research" class="mt-4 inline-block text-indigo-600 font-bold">جرب الآن →</a>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow card-hover text-center">
                    <i class="fa-solid fa-pen-fancy text-4xl text-emerald-600 mb-3"></i>
                    <h3 class="text-xl font-bold">إعادة الصياغة</h3>
                    <p class="text-gray-500 mt-2">صياغة بشرية متقنة لتجنب نسب الاستلال</p>
                    <a href="/tools/paraphrase" class="mt-4 inline-block text-emerald-600 font-bold">جرب الآن →</a>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow card-hover text-center">
                    <i class="fa-solid fa-diagram-project text-4xl text-amber-600 mb-3"></i>
                    <h3 class="text-xl font-bold">خطة البحث</h3>
                    <p class="text-gray-500 mt-2">منهجية أكاديمية متكاملة ومخصصة حسب عنوان بحثك</p>
                    <a href="/tools/plan" class="mt-4 inline-block text-amber-600 font-bold">جرب الآن →</a>
                </div>
            </div>
            <div>
                <h2 class="text-2xl font-bold border-r-4 border-indigo-600 pr-3 mb-6">📖 أحدث المقالات والأخبار الأكاديمية</h2>
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
        <footer class="bg-white border-t py-6 text-center text-gray-500 text-sm mt-12">© 2026 منصة الإنجاز</footer>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# ------------------- صفحات الأدوات -------------------
@app.get("/tools/research", response_class=HTMLResponse)
async def tool_research():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html dir="rtl">
    <head><meta charset="UTF-8"><title>الباحث الأكاديمي</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="p-6 bg-gray-50"><a href="/" class="text-indigo-600 font-bold">← العودة للرئيسية</a>
    <div class="bg-white p-6 rounded shadow mt-4 max-w-2xl mx-auto"><input id="q" class="border p-2 w-full rounded" placeholder="أدخل موضوع البحث..."><button onclick="search()" class="bg-indigo-600 text-white p-2 mt-2 w-full rounded font-bold">بحث واستخراج المصادر</button><div id="res" class="mt-4 space-y-2"></div></div>
    <script>async function search(){let q=document.getElementById('q').value;let r=await fetch('/api/research_iraqi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q})});let d=await r.json();let html='';if(d.sources){d.sources.forEach(s=>{html+=`<div class='p-3 border rounded bg-gray-50'><b>${s.title}</b><br><span class='text-sm text-gray-600'>${s.authors} (${s.year})</span><br><a href='${s.pdf_url||s.url}' target='_blank' class='text-indigo-600 text-sm font-bold underline'>تحميل PDF</a></div>`;});}else{html='<p class="text-red-500">لم يتم العثور على نتائج</p>';}document.getElementById('res').innerHTML=html;}</script></body></html>
    """)

@app.get("/tools/paraphrase", response_class=HTMLResponse)
async def tool_paraphrase():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html dir="rtl"><head><meta charset="UTF-8"><title>إعادة الصياغة الأكاديمية</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="p-6 bg-gray-50"><a href="/" class="text-indigo-600 font-bold">← العودة للرئيسية</a><div class="bg-white p-6 rounded shadow mt-4 max-w-2xl mx-auto"><textarea id="txt" rows="6" class="border w-full p-2 rounded" placeholder="أدخل النص الأكاديمي هنا..."></textarea><button onclick="para()" class="bg-indigo-600 text-white p-2 mt-2 w-full rounded font-bold">إعادة الصياغة الفورية</button><div id="out" class="mt-4 p-3 bg-gray-50 border rounded min-h-[100px] whitespace-pre-wrap"></div></div>
    <script>async function para(){let t=document.getElementById('txt').value;let r=await fetch('/api/paraphrase',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});let d=await r.json();document.getElementById('out').innerHTML=d.rewritten_text||'حدث خطأ في معالجة النص';}</script></body></html>
    """)

@app.get("/tools/plan", response_class=HTMLResponse)
async def tool_plan():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html dir="rtl"><head><meta charset="UTF-8"><title>إنشاء خطة البحث</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="p-6 bg-gray-50"><a href="/" class="text-indigo-600 font-bold">← العودة للرئيسية</a><div class="bg-white p-6 rounded shadow mt-4 max-w-2xl mx-auto"><input id="title" class="border p-2 w-full rounded" placeholder="عنوان البحث المقترح..."><button onclick="gen()" class="bg-indigo-600 text-white p-2 mt-2 w-full rounded font-bold">بناء هيكلية وخطة البحث</button><div id="out" class="mt-4 p-3 bg-gray-50 border rounded min-h-[100px] whitespace-pre-wrap"></div></div>
    <script>async function gen(){let t=document.getElementById('title').value;let r=await fetch('/api/research_plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:t})});let d=await r.json();document.getElementById('out').innerHTML=d.plan||'تعذر إنشاء الخطة، يرجى المحاولة لاحقاً';}</script></body></html>
    """)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
