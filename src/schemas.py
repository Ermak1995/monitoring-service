from pydantic import BaseModel


class ServerStatus(BaseModel):
    id: int
    name: str
    hostname: str
    port: int
    is_connected: bool
    status_message: str