from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from models.group import Group
from models.group_member import GroupMember
from models.revoked_token import RevokedToken
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from utils.jwt import SECRET_KEY, ALGORITHM
from fastapi.security import APIKeyHeader

oauth2_scheme = APIKeyHeader(name="Authorization")

def is_active_group(id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if not group.is_active:
        raise HTTPException(status_code=400, detail="Group is not active")
    
    return group

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if db.query(RevokedToken).filter_by(token=token).first():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


def is_admin_or_higher(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GroupMember:
 
    member = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=id).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
 
    if member.role_id not in (1, 2):  
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges. Admin or Super-admin role required"
        )
    
    return member   

def is_super_admin(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> GroupMember:
    member = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Either group not found or you are not a member of this group"
        )
    
    if member.role_id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins allowed"
        ) 
    return member

def is_active_group(id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if not group.is_active:
        raise HTTPException(status_code=400, detail="Group is not active")
    
    return group