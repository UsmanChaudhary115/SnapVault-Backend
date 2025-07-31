from database import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class GroupClaim(Base):
    __tablename__ = "group_claims"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, unique=True, nullable=False)
 
    roles = relationship("GroupRoleClaim", back_populates="claim")
