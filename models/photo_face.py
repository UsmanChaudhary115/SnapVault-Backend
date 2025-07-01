from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class PhotoFace(Base):
    __tablename__ = "photo_faces"

    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    emotion = Column(String, nullable=True)
    confidence = Column(Float, nullable=False)

    photo = relationship("Photo", back_populates="faces")
    user = relationship("User", back_populates="faces_in_photos")
