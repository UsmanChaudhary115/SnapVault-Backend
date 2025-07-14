from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from schemas.user import UserOut

class GroupCreate(BaseModel):
    name: str
    description: str

class GroupJoin(BaseModel):
    invite_code: str

class GroupOut(BaseModel):
    id: int
    name: str
    invite_code: str
    created_at: datetime
    description: Optional[str] = None
    creator: UserOut

    class Config:
        from_attributes = True




class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True 
