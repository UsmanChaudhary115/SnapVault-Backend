from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str  

class UpdateUser(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    bio: Optional[str]
    created_at: datetime
    profile_picture: Optional[str] = None
 
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class Config:
    from_attributes = True