from datetime import datetime

from pydantic import BaseModel


class ServerStatus(BaseModel):
    id: int
    name: str
    hostname: str
    port: int
    is_connected: bool
    status_message: str


class Metric(BaseModel):
    server_id: int
    timestamp: datetime
    cpu: str
    memory: str
    disk: str
