from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from database import get_db
from models.photo import Photo
from models.group_member import GroupMember
from models.user import User
from models.group import Group
from utils.auth_utils import get_current_user
from schemas.photo import PhotoOut
import uuid
import os

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Make sure directory exists


# ✅ Upload a photo to a group
@router.post("/upload", response_model=PhotoOut)
async def upload_photo(
    group_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is a group member
    is_member = db.query(GroupMember).filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this group.")

    # Validate file extension
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Only JPG and PNG files are allowed.")

    # Save file to disk
    filename = f"{uuid.uuid4()}.{ext}"
    save_path = os.path.join(UPLOAD_DIR, filename)

    with open(save_path, "wb") as f:
        f.write(await file.read())

    # Create photo entry in DB
    photo = Photo(
        group_id=group_id,
        uploader_id=current_user.id,
        file_path=save_path
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return photo


# ✅ Get all photos in a group
@router.get("/group/{group_id}", response_model=list[PhotoOut])
def get_group_photos( group_id: int = Path(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_group = db.query(Group).filter(Group.id == group_id).first()
    if not is_group:
        raise HTTPException(status_code=404, detail="Group not found")
    # Ensure user is a member
    is_member = db.query(GroupMember).filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this group.")

    photos = db.query(Photo).filter_by(group_id=group_id).all()
    return photos


# ✅ Get a single photo by ID
@router.get("/{photo_id}", response_model=PhotoOut)
def get_photo(
    photo_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Optional: check if current_user is member of the group where photo was posted
    is_member = db.query(GroupMember).filter_by(
        user_id=current_user.id,
        group_id=photo.group_id
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not allowed to view this photo")

    return photo
