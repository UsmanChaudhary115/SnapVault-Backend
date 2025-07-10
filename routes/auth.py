from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.revoked_token import RevokedToken
from schemas.user import UserCreate, UserLogin, UserOut, PasswordUpdate
from utils.hash import hash_password, verify_password
from utils.jwt import create_access_token
from utils.auth_utils import get_current_user
from passlib.context import CryptContext

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

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password),
        bio="",
        face_embedding=None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}


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


    # Check if token already revoked
    if db.query(RevokedToken).filter_by(token=auth_header).first():
        raise HTTPException(status_code=400, detail="Token already revoked")

    # Save token in revoked table
    db.add(RevokedToken(token=auth_header))
    db.commit()

    return {"message": "Logged out successfully"}
