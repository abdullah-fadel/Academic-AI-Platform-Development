from sqlalchemy.orm import Session
from models import SessionLocal, Visit
from datetime import datetime, timedelta
from fastapi import APIRouter

router = APIRouter(tags=["visits"])

def get_visit_stats():
    db = SessionLocal()
    # إجمالي الزوار
    total = db.query(Visit).count()
    # زوار اليوم
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today = db.query(Visit).filter(Visit.visited_at >= today_start).count()
    # آخر 7 أيام
    week_ago = datetime.now() - timedelta(days=7)
    last_week = db.query(Visit).filter(Visit.visited_at >= week_ago).count()
    # المسارات الأكثر زيارة
    paths = db.query(Visit.path, func.count(Visit.id)).group_by(Visit.path).order_by(func.count(Visit.id).desc()).limit(5).all()
    db.close()
    return {
        "total": total,
        "today": today,
        "last_week": last_week,
        "top_paths": [{"path": p[0], "count": p[1]} for p in paths]
    }
