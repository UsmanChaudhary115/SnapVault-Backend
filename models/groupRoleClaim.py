from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class GroupRoleClaim(Base):
    __tablename__ = "group_roleclaims"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    role_id = Column(Integer, ForeignKey("group_roles.id"), nullable=False)
    claim_id = Column(Integer, ForeignKey("group_claims.id"), nullable=False)

    role = relationship("GroupRole", back_populates="claims")
    claim = relationship("GroupClaim", back_populates="roles")
