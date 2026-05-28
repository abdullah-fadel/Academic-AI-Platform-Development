from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from routers import research_iraqi, paraphrase, research_plan, admin
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
app.include_router(research_iraqi.router, prefix="/api")
app.include_router(paraphrase.router, prefix="/api")
app.include_router(research_plan.router, prefix="/api")
app.include_router(admin.router, prefix="/admin")

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

# ------------------- الصفحة الرئيسية -------------------
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
    </head>
    <body class="bg-gray-50">
        <nav class="bg-white shadow p-4 flex flex-wrap justify-between items-center">
            <h1 class="text-2xl font-bold text-indigo-700">📚 مكتبة الإنجاز</h1>
            <div class="flex gap-4 flex-wrap">
                <a href="/" class="text-indigo-600">الرئيسية</a>
                <a href="/tools/research" class="text-indigo-600">🔍 الباحث العراقي</a>
                <a href="/tools/paraphrase" class="text-indigo-600">✍️ إعادة الصياغة</a>
                <a href="/tools/plan" class="text-indigo-600">📝 خطة البحث</a>
                <a href="/admin/dashboard" class="bg-gray-200 px-3 py-1 rounded">👑 الأدمن</a>
            </div>
        </nav>
        <div class="max-w-6xl mx-auto p-6">
            <div class="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-2xl p-10 text-center">
                <h2 class="text-4xl font-black">الذكاء الاصطناعي للبحث الأكاديمي</h2>
                <p class="text-lg mt-4">استخرج المصادر، أعد صياغة النصوص، واكتب خطط بحثك بكل احترافية.</p>
                <div class="mt-6 flex justify-center gap-4">
                    <span class="bg-white/20 px-4 py-2 rounded-full">📊 زوار اليوم: {today_visits}</span>
                    <span class="bg-white/20 px-4 py-2 rounded-full">👥 إجمالي الزوار: {total_visits}</span>
                </div>
            </div>
            <div class="mt-12">
                <h3 class="text-2xl font-bold border-b pb-2">📖 أحدث المقالات</h3>
                <div class="grid md:grid-cols-2 gap-6 mt-6">
    """
    for art in articles:
        html += f"""
        <div class="bg-white p-5 rounded-xl shadow">
            <h4 class="font-bold text-xl">{art.title}</h4>
            <p class="text-gray-600 mt-2">{art.content[:150]}...</p>
            <small class="text-gray-400">{art.created_at.strftime('%Y-%m-%d')}</small>
        </div>
        """
    html += """
                </div>
            </div>
        </div>
        <footer class="bg-white border-t p-4 text-center text-gray-500 mt-12">جميع الحقوق محفوظة © مكتبة الإنجاز</footer>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# ------------------- صفحات الأدوات (منفصلة) -------------------
@app.get("/tools/research", response_class=HTMLResponse)
async def tool_research():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>الباحث العراقي - مكتبة الإنجاز</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    </head>
    <body class="bg-gray-100 p-6">
        <div class="max-w-5xl mx-auto">
            <a href="/" class="inline-block mb-4 text-indigo-600"><i class="fas fa-arrow-right"></i> العودة للرئيسية</a>
            <div class="bg-white rounded-2xl shadow-xl p-6">
                <h1 class="text-2xl font-bold">🔍 الباحث العراقي - استخراج أحدث المصادر العلمية</h1>
                <p class="text-gray-500 mt-2">ابحث عن عنوان أو مجال، وسنعرض لك 20 مصدراً حديثاً (2021-2025) مع روابط PDF.</p>
                <div class="mt-6 flex gap-2">
                    <input type="text" id="queryInput" placeholder="أدخل عنوان البحث..." class="flex-1 border p-3 rounded-xl">
                    <button onclick="searchSources()" class="bg-indigo-600 text-white px-6 py-3 rounded-xl">بحث</button>
                </div>
                <div id="results" class="mt-8 space-y-4"></div>
            </div>
        </div>
        <script>
            async function searchSources() {
                const query = document.getElementById('queryInput').value.trim();
                if(!query) return Swal.fire('خطأ', 'الرجاء إدخال عنوان البحث', 'error');
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="text-center py-10">جاري البحث عن أحدث المصادر...</div>';
                try {
                    const res = await fetch('/api/research_iraqi', {
                        method: 'POST',
                        headers: {'Content-Type':'application/json'},
                        body: JSON.stringify({query})
                    });
                    const data = await res.json();
                    if(!data.sources || data.sources.length===0) {
                        resultsDiv.innerHTML = '<div class="bg-yellow-50 p-4 rounded">لا توجد مصادر حديثة. حاول تغيير الكلمات المفتاحية.</div>';
                        return;
                    }
                    let html = '<div class="space-y-4">';
                    data.sources.forEach(s => {
                        html += `
                        <div class="border rounded-xl p-4 hover:shadow transition">
                            <h3 class="font-bold text-lg">${s.title}</h3>
                            <p class="text-sm text-gray-600">${s.authors} | ${s.year} | ${s.journal}</p>
                            <p class="text-gray-500 text-sm mt-1">${s.abstract.substring(0,200)}...</p>
                            <div class="mt-3 flex gap-3">
                                <a href="${s.url}" target="_blank" class="text-indigo-600">🔗 تفاصيل</a>
                                ${s.pdf_url ? `<a href="${s.pdf_url}" target="_blank" class="text-green-600">📄 تحميل PDF</a>` : ''}
                            </div>
                        </div>
                        `;
                    });
                    html += '</div>';
                    resultsDiv.innerHTML = html;
                } catch(e) {
                    Swal.fire('خطأ', 'فشل الاتصال بالخادم', 'error');
                }
            }
        </script>
    </body>
    </html>
    """)

@app.get("/tools/paraphrase", response_class=HTMLResponse)
async def tool_paraphrase():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>إعادة الصياغة - مكتبة الإنجاز</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    </head>
    <body class="bg-gray-100 p-6">
        <div class="max-w-4xl mx-auto">
            <a href="/" class="inline-block mb-4 text-indigo-600"><i class="fas fa-arrow-right"></i> العودة للرئيسية</a>
            <div class="bg-white rounded-2xl shadow-xl p-6">
                <h1 class="text-2xl font-bold">✍️ إعادة صياغة النصوص بطريقة بشرية أكاديمية</h1>
                <p class="text-gray-500 mt-1">الصق النص الأكاديمي (بدون حدود) وسنقوم بإعادة صياغته بشكل احترافي.</p>
                <textarea id="originalText" rows="8" class="w-full border rounded-xl p-4 mt-4" placeholder="ضع النص هنا..."></textarea>
                <div class="flex gap-3 mt-4">
                    <button onclick="clearText()" class="bg-gray-200 px-4 py-2 rounded">مسح النص</button>
                    <button onclick="copyText()" class="bg-blue-600 text-white px-4 py-2 rounded">نسخ النص</button>
                    <button onclick="paraphrase()" class="bg-indigo-600 text-white px-6 py-2 rounded flex-1">إعادة الصياغة</button>
                </div>
                <div id="resultArea" class="mt-6 hidden">
                    <h3 class="font-bold">النص المعاد صياغته:</h3>
                    <div id="resultText" class="bg-gray-50 p-4 rounded border mt-2 whitespace-pre-wrap"></div>
                </div>
            </div>
        </div>
        <script>
            async function paraphrase() {
                const text = document.getElementById('originalText').value;
                if(!text.trim()) return Swal.fire('خطأ', 'الرجاء إدخال النص', 'error');
                const resultDiv = document.getElementById('resultArea');
                const resultText = document.getElementById('resultText');
                resultDiv.classList.remove('hidden');
                resultText.innerHTML = 'جارٍ العمل...';
                try {
                    const res = await fetch('/api/paraphrase', {
                        method: 'POST',
                        headers: {'Content-Type':'application/json'},
                        body: JSON.stringify({text})
                    });
                    const data = await res.json();
                    if(data.rewritten_text) {
                        resultText.innerHTML = data.rewritten_text.replace(/\\n/g, '<br>');
                    } else {
                        resultText.innerHTML = 'حدث خطأ في الخادم';
                    }
                } catch(e) {
                    resultText.innerHTML = 'فشل الاتصال';
                }
            }
            function clearText() { document.getElementById('originalText').value = ''; }
            function copyText() {
                const text = document.getElementById('originalText').value;
                navigator.clipboard.writeText(text);
                Swal.fire('تم النسخ', '', 'success');
            }
        </script>
    </body>
    </html>
    """)

@app.get("/tools/plan", response_class=HTMLResponse)
async def tool_plan():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>كتابة خطة البحث - مكتبة الإنجاز</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    </head>
    <body class="bg-gray-100 p-6">
        <div class="max-w-4xl mx-auto">
            <a href="/" class="inline-block mb-4 text-indigo-600"><i class="fas fa-arrow-right"></i> العودة للرئيسية</a>
            <div class="bg-white rounded-2xl shadow-xl p-6">
                <h1 class="text-2xl font-bold">📝 كتابة خطة بحث منهجية متكاملة</h1>
                <p class="text-gray-500">أدخل عنوان بحثك وسيقوم الذكاء الاصطناعي بإنشاء خطة بحث مفصلة.</p>
                <input type="text" id="titleInput" placeholder="مثال: أثر الذكاء الاصطناعي على التعليم الجامعي" class="w-full border p-3 rounded-xl mt-4">
                <div class="flex gap-3 mt-4">
                    <button onclick="clearTitle()" class="bg-gray-200 px-4 py-2 rounded">مسح</button>
                    <button onclick="copyTitle()" class="bg-blue-600 text-white px-4 py-2 rounded">نسخ العنوان</button>
                    <button onclick="generatePlan()" class="bg-indigo-600 text-white px-6 py-2 rounded flex-1">إنشاء الخطة</button>
                </div>
                <div id="planResult" class="mt-6 hidden">
                    <h3 class="font-bold">📋 خطة البحث:</h3>
                    <div id="planText" class="bg-gray-50 p-4 rounded border mt-2 whitespace-pre-wrap"></div>
                    <button onclick="copyPlan()" class="mt-3 bg-green-600 text-white px-4 py-2 rounded">نسخ الخطة</button>
                </div>
            </div>
        </div>
        <script>
            async function generatePlan() {
                const title = document.getElementById('titleInput').value.trim();
                if(!title) return Swal.fire('خطأ', 'الرجاء إدخال عنوان البحث', 'error');
                const resultDiv = document.getElementById('planResult');
                const planText = document.getElementById('planText');
                resultDiv.classList.remove('hidden');
                planText.innerHTML = 'جارٍ إنشاء خطة البحث ...';
                try {
                    const res = await fetch('/api/research_plan', {
                        method: 'POST',
                        headers: {'Content-Type':'application/json'},
                        body: JSON.stringify({title})
                    });
                    const data = await res.json();
                    if(data.plan) {
                        planText.innerHTML = data.plan.replace(/\\n/g, '<br>');
                    } else {
                        planText.innerHTML = 'حدث خطأ في التوليد';
                    }
                } catch(e) {
                    planText.innerHTML = 'فشل الاتصال بالخادم';
                }
            }
            function clearTitle() { document.getElementById('titleInput').value = ''; }
            function copyTitle() {
                const t = document.getElementById('titleInput').value;
                navigator.clipboard.writeText(t);
                Swal.fire('تم نسخ العنوان', '', 'success');
            }
            function copyPlan() {
                const plan = document.getElementById('planText').innerText;
                navigator.clipboard.writeText(plan);
                Swal.fire('تم نسخ الخطة', '', 'success');
            }
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
