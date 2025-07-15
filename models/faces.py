from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Face(Base):
    __tablename__ = "faces"

    id = Column(Integer, primary_key=True, index=True)
    embedding = Column(String, nullable=False)    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)   
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True) #for now

    user = relationship("User", back_populates="faces")
    photos = relationship("PhotoFace", back_populates="face")