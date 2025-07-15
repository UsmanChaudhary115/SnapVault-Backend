import random, string
from fastapi import APIRouter, Depends, HTTPException, Path # type: ignore
from schemas.user import UserOut
from sqlalchemy.orm import Session # type: ignore
from database import get_db
from models.group import Group
from models.group_member import GroupMember
from schemas.group import GroupCreate, GroupJoin, GroupOut, GroupUpdate
from utils.auth_utils import get_current_user
from models.user import User

router = APIRouter()
 
@router.get("allGroups", response_model=list[GroupOut])
def get_all_groups(db: Session = Depends(get_db)):
    groups = db.query(Group).all()
    return groups

@router.get("/allAppUsers", response_model=list[UserOut])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users