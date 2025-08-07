from fastapi import HTTPException
from fastapi import APIRouter, Depends, status #type: ignore
from sqlalchemy.orm import Session  #type: ignore
from constants import BACKBLAZE_BUCKET_NAME
from database import get_db
from models.faces import Face
from models.photo import Photo
from models.photo_face import PhotoFace
from models.user import User 
from models.group import Group
from models.group_member import GroupMember
from schemas.user import UserOut, UpdateUser, PasswordUpdate
from utils.auth_utils import get_current_user 
from email_validator import validate_email, EmailNotValidError 
from utils.backBlaze_utils import generate_presigned_url
from utils.hash import verify_password, hash_password
from utils.backBlaze_utils import s3_client
from constants import BACKBLAZE_BUCKET_NAME, MAX_FILE_SIZE_BYTES_PROFILE_PICTURE

router = APIRouter()
@router.put("/bio/{updatedBio}", response_model=UserOut)
def update_bio(updatedBio: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.bio = updatedBio
    db.commit()
    db.refresh(current_user) 
    return current_user

@router.get("/profile", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    current_user.profile_picture = generate_presigned_url(BACKBLAZE_BUCKET_NAME, current_user.profile_picture)
    return current_user


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
    if not updatedUser.password:
        raise HTTPException(status_code=400, detail="Current password is required")
    try:
        validate_email(updatedUser.email, check_deliverability=False) # Validate email format without checking deliverability
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    updatedUser.email = updatedUser.email.strip().lower()
    if(updatedUser.email == current_user.email):
        raise HTTPException(status_code=400, detail="New email cannot be the same as the current email")

    if db.query(User).filter(User.email == updatedUser.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    if not verify_password(updatedUser.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
     
    
    current_user.email = updatedUser.email 
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/delete", status_code=status.HTTP_200_OK)
def delete_user(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): 
    owned_memberships = db.query(GroupMember).filter_by(user_id=current_user.id, role_id=1).all()
    owned_group_ids = {m.group_id for m in owned_memberships}
    
    for owned_group_id in owned_group_ids:
        group = db.query(Group).filter(Group.id == owned_group_id).first()
        if group:
            db.query(GroupMember).filter(GroupMember.group_id == group.id).delete() 
            db.delete(group)
    
    db.commit()
    remaining_groups = db.query(GroupMember).filter(GroupMember.user_id == current_user.id, ~GroupMember.group_id.in_(owned_group_ids)).all()
    for membership in remaining_groups:
        db.delete(membership)
    
    db.delete(current_user)
    db.commit()
    try:
        s3_client.delete_object(Bucket=BACKBLAZE_BUCKET_NAME, Key=current_user.profile_picture)
    except Exception as e:
        print(f"Failed to delete profile picture from S3: {e}")

    return {"message": "User, created groups, and memberships deleted successfully."}


@router.put("/update-password")
def update_password(
    data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
        # Checking if current password is correct  
        if not verify_password(data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Preventing reuse of old password
        if verify_password(data.new_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from the current password"
            )
 

        # Hashing and updating the new password
        hashed_new_password = hash_password(data.new_password)
        current_user.hashed_password = hashed_new_password
        db.commit()
        db.refresh(current_user)

        return {"message": "Password updated successfully"}


@router.get("/user_stats")
def get_user_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_groups = db.query(GroupMember).filter(GroupMember.user_id == current_user.id).count()

    face = db.query(Face).filter(Face.user_id == current_user.id).first()
    total_photos = 0

    if face:
        total_photos = db.query(PhotoFace).filter(PhotoFace.face_id == face.id).count()

    return {
        "total_groups": total_groups,
        "total_photos": total_photos
    }
