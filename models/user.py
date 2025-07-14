from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    bio = Column(String, default="Hey there, I'm using SnapVault!") 

    hashed_password = Column(String, nullable=False)
    profile_picture = Column(String, nullable=True)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    created_groups = relationship("Group", back_populates="creator")
    joined_groups = relationship("GroupMember", back_populates="user")
    uploaded_photos = relationship("Photo", back_populates="uploader")
    faces = relationship("Face", back_populates="user")