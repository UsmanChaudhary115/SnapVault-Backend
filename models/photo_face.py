from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class PhotoFace(Base):
    __tablename__ = "photo_faces"

    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    face_id = Column(Integer, ForeignKey("faces.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True) # for now

    photo = relationship("Photo", back_populates="faces")
    face = relationship("Face", back_populates="photos")