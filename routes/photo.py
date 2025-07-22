import json
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from database import get_db
from models.group_member import GroupMember
from models.photo_face import PhotoFace
from models.user import User
from models.group import Group
from utils.auth_utils import get_current_user, is_admin_or_higher
from schemas.photo import PhotoOut
import uuid
import os 
import cv2
import numpy as np  
from models import Photo, GroupMember, Face  
from insightface.app import FaceAnalysis
from sklearn.metrics.pairwise import cosine_similarity

 

face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0)

router = APIRouter()

UPLOAD_DIR = "uploads/photos" 
THRESHOLD = 0.6

 
# @router.post("/upload", response_model=List[PhotoOut])
# async def upload_photos(
#     group_id: int = Form(...),
#     files: List[UploadFile] = File(...),
#     db: Session = Depends(get_db),
#     caller = Depends(is_admin_or_higher)
# ):
#     member = db.query(GroupMember).filter_by(
#         user_id=caller.id,
#         group_id=group_id
#     ).first()   
#     if not member.role_id in [1, 2, 3]:  # Assuming roles 1, 2 and 3 are allowed to upload photos
#         raise HTTPException(status_code=403, detail="You are not allowed to upload photos to this group.")

 
#     ext = file.filename.split(".")[-1].lower()
#     if ext not in ["jpg", "jpeg", "png"]:
#         raise HTTPException(status_code=400, detail="Only JPG and PNG files are allowed.")

 
#     filename = f"{uuid.uuid4()}.{ext}"
#     save_path = os.path.join(UPLOAD_DIR, filename)

#     with open(save_path, "wb") as f:
#         f.write(await file.read())

 
#     photo = Photo(
#         group_id=group_id,
#         uploader_id=caller.id,
#         file_path=save_path
#     )
#     db.add(photo)
#     db.commit()
#     db.refresh(photo)

#     return photo





@router.post("/upload", response_model=List[PhotoOut])
async def upload_photos(
    group_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    member = db.query(GroupMember).filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    print(f"Current user ID: {current_user.id}, Group ID: {group_id}")
    print(f"Member: {member}, Role ID: {member.role_id if member else 'None'}")
    if not member or member.role_id not in [1, 2, 3]:
        raise HTTPException(status_code=403, detail="You are not allowed to upload photos to this group.")

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    photos_out = []

    for file in files:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png"]:
            raise HTTPException(status_code=400, detail="Only JPG and PNG files are allowed.")

        filename = f"{uuid.uuid4()}.{ext}"
        save_path = os.path.join(UPLOAD_DIR, filename)

        with open(save_path, "wb") as f:
            f.write(await file.read())

        # Add photo entry
        photo = Photo(
            group_id=group_id,
            uploader_id=current_user.id,
            file_path=save_path
        )
        db.add(photo)
        db.commit()
        db.refresh(photo)
        photos_out.append(photo)

        # Detect faces
        img = cv2.imread(save_path)
        faces = face_app.get(img)

        all_faces = db.query(Face).all()

        for face in faces:
            embedding = face.embedding  # numpy array

            found_match = False
            for existing in all_faces:
                existing_embedding = np.array(json.loads(existing.embedding), dtype=np.float32)
                sim = cosine_similarity([embedding], [existing_embedding])[0][0]
                if sim >= THRESHOLD:
                    # Update embedding by averaging
                    new_embedding = (embedding + existing_embedding) / 2
                    existing.embedding = json.dumps(new_embedding.tolist())
                    db.commit()

                    # Create association record linking this face with current photo
                    association = PhotoFace(photo_id=photo.id, face_id=existing.id)
                    db.add(association)
                    db.commit()

                    found_match = True
                    break

            if not found_match:
                # New face record
                new_face = Face(
                    user_id=None,
                    embedding=json.dumps(embedding.tolist())
                )
                db.add(new_face)
                db.commit()
                db.refresh(new_face)

                # Link new face with current photo
                association = PhotoFace(photo_id=photo.id, face_id=new_face.id)
                db.add(association)
                db.commit()

    return photos_out

@router.get("/group/{group_id}", response_model=list[PhotoOut])
def get_group_photos(group_id: int = Path(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_group = db.query(Group).filter(Group.id == group_id).first()
    if not is_group:
        raise HTTPException(status_code=404, detail="Group not found")
 
    member = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=group_id).first()
    if not member or member.role_id not in [1, 2, 3, 4]:  # Assuming roles 1, 2, 3, and 4 can view all photos
        raise HTTPException(status_code=403, detail="You are not allowed to view photos in this group")

    photos = db.query(Photo).filter_by(group_id=group_id).all()
    return photos

@router.get("/my/photos/all", response_model=list[PhotoOut])
def get_my_photos(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    face = db.query(Face).filter(Face.user_id == current_user.id).first()
    if not face:
        raise HTTPException(status_code=404, detail="Face not found for the current user")
    photo_faces = db.query(PhotoFace).filter(PhotoFace.face_id == face.id).all()
    photos = db.query(Photo).filter(Photo.id.in_([pf.photo_id for pf in photo_faces])).all() 
    return photos


@router.get("/my/photos/{group_id}", response_model=list[PhotoOut])
def get_my_photos_in_group(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
 
    # memberShip = db.query(GroupMember).filter_by(
    #     user_id=current_user.id,
    #     group_id=group_id
    # ).first() 

    # if not memberShip:   
    #     raise HTTPException(status_code=403, detail="You are not allowed to view photos in this group")
    
    user_face = db.query(Face).filter(Face.user_id == current_user.id).first()
    if not user_face:
        raise HTTPException(404, "No face found for this user")

    matched_photo_ids = (
        db.query(PhotoFace.photo_id)
        .filter(PhotoFace.face_id == user_face.id)
        .all()
    )
    matched_photo_ids = [pid[0] for pid in matched_photo_ids]

    matched_photos = (
        db.query(Photo)
        .filter(Photo.group_id == group_id, Photo.id.in_(matched_photo_ids))
        .all()
    )

    return matched_photos


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

