# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine

from app.logging_config import logger
# from app.models import Base


DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/monitoring"
# DATABASE_URL = "postgresql+asyncpg://mon_admin@127.0.0.1/monitoring"
logger.info("Создание движка базы данных с URL: %s", DATABASE_URL)
engine = create_async_engine(DATABASE_URL, echo=True)
