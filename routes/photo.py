from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from database import get_db
from models.photo import Photo
from models.photo_face import PhotoFace
from models.faces import Face
from models.group_member import GroupMember
from models.user import User
from models.group import Group
from utils.auth_utils import get_current_user
from schemas.photo import PhotoOut
import uuid
import os

router = APIRouter()

UPLOAD_DIR = "uploads/photos" 

 
@router.post("/upload", response_model=PhotoOut)
async def upload_photo(group_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
 
    is_member = db.query(GroupMember).filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this group.")

 
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Only JPG and PNG files are allowed.")

 
    filename = f"{uuid.uuid4()}.{ext}"
    save_path = os.path.join(UPLOAD_DIR, filename)

    with open(save_path, "wb") as f:
        f.write(await file.read())

 
    photo = Photo(
        group_id=group_id,
        uploader_id=current_user.id,
        file_path=save_path
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return photo

 
@router.get("/group/{group_id}", response_model=list[PhotoOut])
def get_group_photos( group_id: int = Path(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_group = db.query(Group).filter(Group.id == group_id).first()
    if not is_group:
        raise HTTPException(status_code=404, detail="Group not found")
 
    is_member = db.query(GroupMember).filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this group.")

    photos = db.query(Photo).filter_by(group_id=group_id).all()
    return photos

@router.get("/my", response_model=list[PhotoOut])
def get_my_photos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        face = db.query(Face).filter(Face.user_id == current_user.id).first()
        if not face:
            raise HTTPException(status_code=404, detail="Face not found for the current user")
        photo_faces = db.query(PhotoFace).filter(PhotoFace.face_id == face.id).all()
        photos = db.query(Photo).filter(Photo.id.in_([pf.photo_id for pf in photo_faces])).all()
        #file_paths = [db.query(Photo.file_path).filter(Photo.id == pf.photo_id).scalar() for pf in photo_faces]

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    return photos



@router.get("/{photo_id}", response_model=PhotoOut)
def get_photo(
    photo_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
 
    is_member = db.query(GroupMember).filter_by(
        user_id=current_user.id,
        group_id=photo.group_id
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not allowed to view this photo")

    return photo

