from datetime import datetime

from fastapi.security import OAuth2PasswordRequestForm
from paramiko.client import SSHClient, AutoAddPolicy
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import Server, ServerMetric, ServerLog, User

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import select, inspect, insert

from database import Base, engine, SessionLocal, get_db
from schemas import ServerStatus, ServerCreate, UserCreate, ServerUpdate
from auth import get_password_hash, authenticate_user, create_access_token
from auth import get_current_user

app = FastAPI()

Base.metadata.create_all(bind=engine)  # Создает таблицы


@app.get('/servers')
def servers(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return user.servers
    except:
        raise HTTPException(detail='Ошибка в получении данных о серверах')


@app.post('/add_server')
def add_server(data: ServerCreate, db: Session = Depends(get_db)):
    try:
        new_server = Server(**data.dict())
        db.add(new_server)
        db.commit()
        return {"message": "Added Successfully"}
    except:
        raise HTTPException(detail='Не получилось добавить сервер')


# @app.post('/servers')
# def add_servers(data: ServerCreate, db: Session = Depends(get_db)):
#     try:
#         new_server = Server(**data.dict())
#         db.add(new_server)
#         db.commit()
#         return 'Added successfully'
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=f"Ошибка при добавлении сервера: {str(e)}")


@app.get('/servers/{server_id}/check-connection')
def check_connection(server_id: int, db: Session = Depends(get_db)):
    '''
    Проверка возможности подключения к серверу
    '''
    result = db.execute(select(Server).where(Server.id == server_id))
    db_server = result.scalar_one_or_none()

    if db_server is None:
        raise HTTPException(status_code=404, detail="Сервер не найден")

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


@app.get('/servers/{server_id}')
def get_status(server_id: int, db: Session = Depends(get_db)):
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    db_server = db.execute(select(Server).where(Server.id == server_id)).scalar_one_or_none()
    if db_server is None:
        raise HTTPException(status_code=404, detail="Сервер не найден")

    metrics = {}
    logs = []

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

        # Metrics
        for key, cmd in commands.items():
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode('utf-8')
            metrics[key] = float(output) if output else None

        # Logs
        stdin, stdout, stderr = client.exec_command("journalctl -n 20 --no-pager")
        output = stdout.read().decode('utf-8')
        logs.append(output)

        new_metric = ServerMetric(
            server_id=db_server.id,
            timestamp=datetime.utcnow(),
            cpu=metrics.get('cpu'),
            memory=metrics.get('memory'),
            disk=metrics.get('disk'),
        )
        new_log = ServerLog(
            server_id=db_server.id,
            timestamp=datetime.utcnow(),
            info=logs,

        )
        db.add(new_metric)
        db.add(new_log)
        db.commit()
        return {
            "server_id": db_server.id,
            "timestamp": new_metric.timestamp,
            "cpu": metrics.get('cpu'),
            "memory": metrics.get('memory'),
            "disk": metrics.get('disk'),
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось получить информацию: {str(e)}")


@app.patch('/servers/{server_id}')
def update_server(server_id: int, data: ServerUpdate, db: Session = Depends(get_db)):
    update_data = data.model_dump(exclude_none=True)  # Преобразование pydantic в dict
    server = db.execute(select(Server).where(Server.id == server_id)).scalar_one_or_none()
    if server is None:
        raise HTTPException(status_code=404, detail="Сервер не найден")
    for field in update_data:
        if field != 'password':
            setattr(server, field, update_data[field])
    try:
        db.add(server)
        db.commit()
        return {"update_server": server}
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail='Не удалось обновить информацию о сервере')


@app.delete('/servers/{server_id}')
def delete_server(server_id: int, db: Session = Depends(get_db)):
    server = db.execute(select(Server).where(Server.id == server_id)).scalar_one_or_none()
    if server is None:
        raise HTTPException(status_code=404, detail="Сервер не найден")
    try:
        name = server.name
        db.delete(server)
        db.commit()
        return {"message": f"Сервер {name} успешно удален"}
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail='Не удалось удалить сервер')


@app.post('/register')
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.execute(select(User).where(User.email == user_data.email)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=401, detail="Пользователь с таким email уже существует")

    hashed_password = get_password_hash(user_data.password)
    try:
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password=hashed_password
        )
        db.add(new_user)
        db.commit()
        return {"message": "Пользователь зарегистрирован", "user_id": new_user.id}
    except:
        db.rollback()
        return {"message": "Ошибка! Пользователь не зарегистрирован"}


@app.post('/login')
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail='Неверные учетные данные')
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "Bearer"}
