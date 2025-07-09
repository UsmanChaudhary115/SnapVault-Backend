from pydantic import BaseModel
from datetime import datetime
from schemas.user import UserOut

class GroupCreate(BaseModel):
    name: str

class GroupJoin(BaseModel):
    invite_code: str

class GroupOut(BaseModel):
    id: int
    name: str
    invite_code: str
    created_at: datetime
    creator: UserOut

class GroupUpdate(BaseModel):
    name: str

class Config:
    from_attributes = True  
