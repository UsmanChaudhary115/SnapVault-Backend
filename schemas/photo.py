from datetime import datetime
from pydantic import BaseModel


class PhotoOut(BaseModel):
    id: int
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True
