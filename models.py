from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Visit(Base):
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String(50))
    user_agent = Column(String(200))
    path = Column(String(100))
    visited_at = Column(DateTime, server_default=func.now())

Base.metadata.create_all(bind=engine)
