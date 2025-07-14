# models/group_role.py
from sqlalchemy import Column, Integer, String
from database import Base

class GroupRole(Base):
    __tablename__ = "group_roles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, unique=True, nullable=False)
