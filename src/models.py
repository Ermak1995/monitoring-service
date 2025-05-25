from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Server(Base):
    __tablename__ = 'servers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    ip_address: Mapped[str] = mapped_column(String(15), unique=True)

    def __repr__(self):
        return f'Server: {self.name} - {self.ip_address}'