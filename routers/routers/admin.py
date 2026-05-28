from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from models import SessionLocal, Article
from routers.visits import get_visit_stats

router = APIRouter(tags=["admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# صفحة لوحة الأدمن
@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    articles = db.query(Article).order_by(Article.created_at.desc()).all()
    stats = get_visit_stats()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>لوحة تحكم الأدمن | مكتبة الإنجاز</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body class="bg-gray-100">
        <div class="max-w-7xl mx-auto p-6">
            <div class="flex justify-between items-center">
                <h1 class="text-3xl font-bold">👑 لوحة تحكم الأدمن</h1>
                <a href="/" class="bg-indigo-600 text-white px-4 py-2 rounded">← العودة للموقع</a>
            </div>
            <!-- إحصائيات -->
            <div class="grid md:grid-cols-3 gap-6 mt-8">
                <div class="bg-white p-4 rounded-xl shadow text-center">
                    <h3 class="text-gray-500">إجمالي الزوار</h3>
                    <p class="text-3xl font-bold">{stats['total']}</p>
                </div>
                <div class="bg-white p-4 rounded-xl shadow text-center">
                    <h3 class="text-gray-500">زوار اليوم</h3>
                    <p class="text-3xl font-bold">{stats['today']}</p>
                </div>
                <div class="bg-white p-4 rounded-xl shadow text-center">
                    <h3 class="text-gray-500">آخر 7 أيام</h3>
                    <p class="text-3xl font-bold">{stats['last_week']}</p>
                </div>
            </div>
            <!-- رسم بياني بسيط (يمكن تحسينه) -->
            <div class="bg-white p-4 rounded-xl shadow mt-8">
                <h3 class="font-bold mb-4">أكثر الصفحات زيارة</h3>
                <canvas id="chart" height="100"></canvas>
            </div>
            <!-- إدارة المقالات -->
            <div class="mt-10">
                <div class="flex justify-between items-center">
                    <h2 class="text-2xl font-bold">📰 إدارة المقالات</h2>
                    <button onclick="showAddForm()" class="bg-green-600 text-white px-4 py-2 rounded">+ إضافة مقال</button>
                </div>
                <div id="addForm" class="hidden mt-4 bg-white p-4 rounded shadow">
                    <form action="/admin/article/create" method="post">
                        <input type="text" name="title" placeholder="عنوان المقال" class="border p-2 w-full rounded mb-2" required>
                        <textarea name="content" placeholder="محتوى المقال" class="border p-2 w-full rounded h-32" required></textarea>
                        <button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded mt-2">نشر</button>
                    </form>
                </div>
                <div class="mt-6 space-y-4">
    """
    for art in articles:
        html += f"""
        <div class="bg-white p-4 rounded shadow flex justify-between items-center">
            <div>
                <h3 class="font-bold">{art.title}</h3>
                <p class="text-sm text-gray-500">{art.created_at.strftime('%Y-%m-%d')}</p>
            </div>
            <div>
                <a href="/admin/article/edit/{art.id}" class="bg-yellow-500 text-white px-3 py-1 rounded inline-block">تعديل</a>
                <a href="/admin/article/delete/{art.id}" onclick="return confirm('حذف؟')" class="bg-red-600 text-white px-3 py-1 rounded">حذف</a>
            </div>
        </div>
        """
    html += """
                </div>
            </div>
        </div>
        <script>
            const ctx = document.getElementById('chart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: """ + str([p['path'] for p in stats['top_paths']]) + """,
                    datasets: [{
                        label: 'عدد الزيارات',
                        data: """ + str([p['count'] for p in stats['top_paths']]) + """,
                        backgroundColor: '#4f46e5'
                    }]
                }
            });
            function showAddForm() {
                document.getElementById('addForm').classList.toggle('hidden');
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# إنشاء مقال
@router.post("/article/create")
async def create_article(title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    article = Article(title=title, content=content)
    db.add(article)
    db.commit()
    return RedirectResponse("/admin/dashboard", status_code=303)

# حذف مقال
@router.get("/article/delete/{article_id}")
async def delete_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if article:
        db.delete(article)
        db.commit()
    return RedirectResponse("/admin/dashboard", status_code=303)

# تعديل مقال (صفحة بسيطة)
@router.get("/article/edit/{article_id}", response_class=HTMLResponse)
async def edit_article_page(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        return HTMLResponse("المقال غير موجود", status_code=404)
    html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>تعديل مقال</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="p-6 bg-gray-100">
        <div class="max-w-2xl mx-auto bg-white p-6 rounded shadow">
            <h1 class="text-2xl font-bold">تعديل المقال</h1>
            <form action="/admin/article/update/{article.id}" method="post" class="mt-4">
                <input type="text" name="title" value="{article.title}" class="border p-2 w-full rounded mb-2" required>
                <textarea name="content" class="border p-2 w-full rounded h-40" required>{article.content}</textarea>
                <button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded mt-2">حفظ التعديلات</button>
            </form>
            <a href="/admin/dashboard" class="text-indigo-600 block mt-4">← العودة</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@router.post("/article/update/{article_id}")
async def update_article(article_id: int, title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if article:
        article.title = title
        article.content = content
        db.commit()
    return RedirectResponse("/admin/dashboard", status_code=303)
