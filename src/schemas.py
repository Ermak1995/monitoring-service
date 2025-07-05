from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class ServerSchema(BaseModel):
    id: int
    name: str
    hostname: str
    port: int = 22
    username: str
    password: str
    is_active: bool = True
    user_id: int

class ServerCreate(BaseModel):
    name: str
    hostname: str
    port: int = 22
    username: str
    password: str
    is_active: bool = True
    user_id: int


class ServerStatus(BaseModel):
    id: int
    name: str
    hostname: str
    port: int
    is_connected: bool
    status_message: str

class ServerUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Если разрешено менять пароль через этот эндпоинт
    is_active: Optional[bool] = None


class Metric(BaseModel):
    server_id: int
    timestamp: datetime
    cpu: str
    memory: str
    disk: str


class Log(BaseModel):
    server_id: int
    timestamp: datetime
    info: str


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str
