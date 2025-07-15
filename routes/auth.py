from email_validator import validate_email, EmailNotValidError
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.revoked_token import RevokedToken
from schemas.user import UserCreate, UserLogin, UserOut, PasswordUpdate
from utils.hash import hash_password, verify_password
from utils.jwt import create_access_token
from utils.auth_utils import get_current_user
from passlib.context import CryptContext   
import uuid
import os

router = APIRouter() 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.put("/update-password")
def update_password(
    data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
        # 1. Check if current password is correct
        if not pwd_context.verify(data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # 2. Prevent reuse of old password
        if pwd_context.verify(data.new_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from the current password"
            )
 

        # 3b. Hash and update
        hashed_new_password = pwd_context.hash(data.new_password)
        current_user.hashed_password = hashed_new_password
        db.commit()
        db.refresh(current_user)

        return {"message": "Password updated successfully"}


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Invalid token header")


 
    if db.query(RevokedToken).filter_by(token=auth_header).first():
        raise HTTPException(status_code=400, detail="Token already revoked")
 
    db.add(RevokedToken(token=auth_header))
    db.commit()

    return {"message": "Logged out successfully"}
