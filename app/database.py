# app/database.py
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://user:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
