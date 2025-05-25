from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

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

    def __repr__(self):
        return f'Server: {self.name} - {self.hostname}'
