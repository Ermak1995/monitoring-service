import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, String, text, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)