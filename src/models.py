from datetime import datetime

from sqlalchemy import String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Server(Base):
    __tablename__ = 'servers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    hostname: Mapped[str] = mapped_column(String(50), unique=True)
    port: Mapped[int] = mapped_column(default=22)
    username: Mapped[str] = mapped_column(String(50))
    password: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))

    metrics = relationship('ServerMetric', back_populates='server', cascade='all, delete')
    logs = relationship('ServerLog', back_populates='server', cascade='all, delete')
    user = relationship('User', back_populates='servers')

    def __repr__(self):
        return f'Server: {self.name} - {self.hostname}'


class ServerMetric(Base):
    __tablename__ = 'metrics'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(ForeignKey('servers.id'))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    cpu: Mapped[str] = mapped_column(Text)
    memory: Mapped[str] = mapped_column(Text)
    disk: Mapped[str] = mapped_column(Text)

    server = relationship('Server', back_populates='metrics')


class ServerLog(Base):
    __tablename__ = 'logs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(ForeignKey('servers.id'))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    info: Mapped[str] = mapped_column(Text)

    server = relationship('Server', back_populates='logs')


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    
    servers = relationship('Server', back_populates='user')
    def __repr__(self):
        return f'User: {self.username}'
