# app/dependencies
from sqlalchemy.ext.asyncio import AsyncSession  # , create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database import engine


async def get_db():
    """Генератор, предоставляющий асинхронную сессию базы данных."""
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
