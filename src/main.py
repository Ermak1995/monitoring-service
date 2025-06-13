from datetime import datetime

from paramiko.client import SSHClient, AutoAddPolicy
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import Server, ServerMetric

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import select, inspect, insert

from database import Base, engine, SessionLocal
from schemas import ServerStatus, ServerCreate

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
        return 'Added successfully'
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка при добавлении сервера: {str(e)}")


@app.get('/servers/{server_id}/check-connection')
def check_connection(server_id: int, db: Session = Depends(get_db)):
    '''
    Проверка возможности подключения к серверу
    '''
    result = db.execute(select(Server).where(Server.id == server_id))
    db_server = result.scalar_one_or_none()

    if db_server is None:
        return HTTPException(status_code=404, detail="Сервер не найден")

    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())

    try:
        client.connect(
            hostname=db_server.hostname,
            port=db_server.port,
            username=db_server.username,
            password=db_server.password
        )
        status_message = "Connected successfully"
        is_connected = True
    except Exception as e:
        status_message = str(e)
        is_connected = False
    finally:
        if client:
            client.close()
    return ServerStatus(
        id=db_server.id,
        name=db_server.name,
        hostname=db_server.hostname,
        port=db_server.port,
        is_connected=is_connected,
        status_message=status_message,
    )


@app.get('/servers/{server_id}/metrics')
def get_metrics(server_id: int, db: Session = Depends(get_db)):
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    db_server = db.execute(select(Server).where(Server.id == server_id)).scalar_one_or_none()
    if db_server is None:
        return HTTPException(status_code=404, detail="Сервер не найден")

    metrics = {}
    commands = {
        "cpu": "grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}'",
        "memory": "free -m | grep Mem | awk '{print $3/$2 * 100.0}'",
        "disk": "df -h / | awk 'NR==2 {print $5}' | sed 's/%//'",
    }

    try:
        client.connect(
            hostname=db_server.hostname,
            port=db_server.port,
            username=db_server.username,
            password=db_server.password
        )
        for key, cmd in commands.items():
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode('utf-8')
            metrics[key] = float(output) if output else None

        new_metric = ServerMetric(
            server_id=db_server.id,
            timestamp=datetime.utcnow(),
            cpu=metrics.get('cpu'),
            memory=metrics.get('memory'),
            disk=metrics.get('disk'),
        )
        db.add(new_metric)
        db.commit()
        return {
            "server_id": db_server.id,
            "timestamp": new_metric.timestamp,
            "cpu": metrics.get('cpu'),
            "memory": metrics.get('memory'),
            "disk": metrics.get('disk'),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось получить метрики: {str(e)}")
