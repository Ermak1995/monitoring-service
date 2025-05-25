from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import Server

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import select, inspect, insert

from database import Base, engine, SessionLocal


class ServerCreate(BaseModel):
    name: str
    ip_address: str


app = FastAPI()

Base.metadata.create_all(bind=engine)  # Создает таблицы


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/servers')
def servers(db: Session = Depends(get_db)):
    return db.execute(select(Server)).scalars().all()


@app.post('/servers')
def add_servers(data: ServerCreate, db: Session = Depends(get_db)):
    try:
        new_server = Server(**data.dict())
        db.add(new_server)
        db.commit()
        return new_server
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при добавлении сервера: {str(e)}"
        )
