import json
from typing import List
import boto3
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Path
from sqlalchemy import or_
from sqlalchemy.orm import Session
from constants import THRESHOLD, UPLOAD_DIR
from database import get_db
from models.group_member import GroupMember
from models.photo_face import PhotoFace
from models.user import User
from models.group import Group
from utils.auth_utils import get_current_user
from schemas.photo import PhotoOut
import uuid, cv2
import numpy as np  
from models import Photo, GroupMember, Face  
from insightface.app import FaceAnalysis
from sklearn.metrics.pairwise import cosine_similarity
from utils.auth_utils import authorize
from constants import *
from utils.highlight_utils import evaluate_image_quality 
from utils.backBlaze_utils import s3_client, generate_presigned_url


face_app = FaceAnalysis(name='buffalo_l', root='./AI Models', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0)
#face_app = FaceAnalysis(name='buffalo_l', root='D:/SnapVault-Backend/AI Models', providers=['CPUExecutionProvider'])
#face_app.prepare(ctx_id=0)

router = APIRouter()

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


    if not member:
        raise HTTPException(status_code=403, detail="You are not authorized to upload photos to this group.")
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    claims = authorize(member.role_id, db)
    if not any(claim.id == CLAIM_UPLOAD_PHOTOS for claim in claims):
        raise HTTPException(status_code=403, detail="You are not authorized to upload photos to this group.")

    photos_out = []

    for file in files:
        ext = file.filename.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png']:
            raise HTTPException(status_code=400, detail="Only JPG, JPEG, PNG allowed.")
        
        filename = f"groups/{group.name}/{uuid.uuid4()}.{ext}" 
        file_content = await file.read()
        file_bytes = np.asarray(bytearray(file_content), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR) 

        try:
            s3_client.put_object(
                Bucket=BACKBLAZE_BUCKET_NAME,
                Key=filename,
                Body=file_content,
                ContentType=file.content_type
         )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error")

        faces = face_app.get(img)
        face_present = True
        if not faces or len(faces) == 0:
            face_present = False
            highlight_status = False
        else:
            score = evaluate_image_quality(faces, img)
            highlight_status = (score >= HIGHLIGHT_THRESHOLD)
        # Add photo entry
        photo = Photo(
            group_id=group_id,
            uploader_id=current_user.id,
            file_path=filename,
            isHighlighted=highlight_status
        )
        db.add(photo)
        db.commit()
        db.refresh(photo)
        photos_out.append(photo)

        # Detecting faces, if any face is present, then add it to the database 
        if face_present == False:
            continue

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
                    existing.embedding_count += 1
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
    if not member:
        raise HTTPException(status_code=403, detail="You are not authorized to view all photos in this group")
    
    claims = authorize(member.role_id, db)
    if not any(claim.id == CLAIM_VIEW_ALL_PHOTOS for claim in claims):
        raise HTTPException(status_code=403, detail="You are not authorized to view all photos in this group")
    
    photos = db.query(Photo).filter_by(group_id=group_id).all()
    if not photos:
        return []
    else:
        for photo in photos:
            photo.file_path = generate_presigned_url(BACKBLAZE_BUCKET_NAME, photo.file_path)
    return photos

@router.get("/my/photos/all", response_model=list[PhotoOut])
def get_my_photos(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    face = db.query(Face).filter(Face.user_id == current_user.id).first()
    if not face:
        raise HTTPException(status_code=404, detail="Face not found for the current user")
    photo_faces = db.query(PhotoFace).filter(PhotoFace.face_id == face.id).all()
    photos = db.query(Photo).filter(Photo.id.in_([pf.photo_id for pf in photo_faces])).all() 
    if not photos:
        return []
    for photo in photos:
        photo.file_path = generate_presigned_url(BACKBLAZE_BUCKET_NAME, photo.file_path)
    return photos


@router.get("/my/photos/{group_id}", response_model=list[PhotoOut])
def get_my_photos_in_group(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
 
    memberShip = db.query(GroupMember).filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first() 

    if not memberShip:   
        raise HTTPException(status_code=403, detail="You are not a member of this group")

    user_face = db.query(Face).filter(Face.user_id == current_user.id).first()
    if not user_face:
        return []

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
    if not matched_photos:
        return []
    for photo in matched_photos:
        photo.file_path = generate_presigned_url(BACKBLAZE_BUCKET_NAME, photo.file_path)
    return matched_photos 

@router.get("/highlights/{group_id}", response_model=list[PhotoOut])
def get_highlighted_photos(group_id: int = Path(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_group = db.query(Group).filter(Group.id == group_id).first()
    if not is_group:    
        raise HTTPException(status_code=404, detail="Group not found")

    member = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=group_id).first()
    if not member:
        raise HTTPException(status_code=403, detail="You are not authorized to view highlighted photos in this group")
    
    photos = db.query(Photo).filter_by(group_id=group_id, isHighlighted=True).all()
    if not photos:
        return []
    else:
        for photo in photos:
            photo.file_path = generate_presigned_url(BACKBLAZE_BUCKET_NAME, photo.file_path)
    return photos

@router.get("/{photo_id}", response_model=PhotoOut)
def get_photo(
    photo_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
 
    is_member = db.query(GroupMember).filter_by(
        user_id=current_user.id,
        group_id=photo.group_id
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not allowed to view this photo")
    
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        return []
    
    photo.file_path = generate_presigned_url(BACKBLAZE_BUCKET_NAME, photo.file_path)

    return photo


@router.delete("/delete/{photo_id}/group/{group_id}", response_model=PhotoOut)
def delete_photo_from_group(
    photo_id: int = Path(..., gt=0),
    group_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),  
    current_user: User = Depends(get_current_user)
):
    is_member = db.query(GroupMember).filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()

    if not is_member:   
        raise HTTPException(status_code=403, detail="You are not authorized to delete this photo from the group")
    
    claims = authorize(is_member.role_id, db)
    if not any(claim.id == CLAIM_DELETE_PHOTOS for claim in claims):
        raise HTTPException(status_code=403, detail="You are not authorized to delete this photo from the group")
    
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.group_id == group_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found in this group")
    try:
        s3_client.delete_object(Bucket=BACKBLAZE_BUCKET_NAME, Key=photo.file_path)
        print(f"Deleted from B2: {photo.file_path}")
    except Exception as e:
        print(f"Failed to delete {photo.file_path} from B2:", e)
    db.delete(photo)
    db.commit()
     
    return photo
