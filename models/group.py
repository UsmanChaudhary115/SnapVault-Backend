from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# models/group.py

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True) 
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)  
    invite_code = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    creator = relationship("User", back_populates="created_groups") 
    members = relationship("GroupMember", back_populates="group") 
    photos = relationship("Photo", back_populates="group", cascade="all, delete-orphan")

