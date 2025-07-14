from http.client import HTTPException
from fastapi import APIRouter, Depends, status #type: ignore
from sqlalchemy.orm import Session  #type: ignore
from database import get_db
from models.user import User 
from models.group import Group
from models.group_member import GroupMember
from schemas.user import UserOut, UpdateUser
from utils.auth_utils import get_current_user 
from email_validator import validate_email, EmailNotValidError
from passlib.context import CryptContext 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




router = APIRouter()
@router.put("/bio/{updatedBio}", response_model=UserOut)
def update_bio(updatedBio: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.bio = updatedBio
    db.commit()
    db.refresh(current_user) 
    return current_user

@router.get("/profile", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

# @router.put("/profile_picture/{profile_picture}", response_model=UserOut)
# def update_profile_picture(profile_picture: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     current_user.profile_picture = profile_picture
#     db.commit()
#     db.refresh(current_user)
#     return current_user
    
@router.put("/name/{name}", response_model=UserOut)
def update_name(name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.name = name
    db.commit()
    db.refresh(current_user)
    return current_user
@router.put("/email", response_model=UserOut)
def update_email(updatedUser: UpdateUser, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
 
    if not updatedUser.email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    try:
        validate_email(updatedUser.email)
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    updatedUser.email = updatedUser.email.strip().upper()
    if(updatedUser.email == current_user.email):
        raise HTTPException(status_code=400, detail="New email cannot be the same as the current email")

    if db.query(User).filter(User.email == updatedUser.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    if not pwd_context.verify(updatedUser.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
     
    
    current_user.email = updatedUser.email 
    db.commit()
    db.refresh(current_user)
    return current_user

@router.delete("/delete", status_code=status.HTTP_200_OK)
def delete_user(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): 
    owned_groups = db.query(Group).filter(Group.creator_id == current_user.id).all()
    for group in owned_groups:
        db.delete(group)
 
    joined_groups = db.query(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    for membership in joined_groups:
        db.delete(membership)
 
    db.delete(current_user)
    db.commit()

    return {"message": "User, created groups, and memberships deleted successfully."}