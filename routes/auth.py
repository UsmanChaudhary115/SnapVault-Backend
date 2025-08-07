from email_validator import validate_email, EmailNotValidError
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from constants import SIMILARITY_THRESHOLD
from database import get_db
from models.faces import Face
from models.user import User
from models.revoked_token import RevokedToken
from schemas.user import UserLogin, UserOut
from utils.hash import hash_password, verify_password
from utils.jwt import create_access_token
from utils.auth_utils import get_current_user   
from sqlalchemy.exc import SQLAlchemyError 
import cv2, uuid, json, os
import numpy as np  
from sklearn.metrics.pairwise import cosine_similarity 
from insightface.app import FaceAnalysis
from utils.backBlaze_utils import s3_client
from constants import BACKBLAZE_BUCKET_NAME, MAX_FILE_SIZE_BYTES_PROFILE_PICTURE
 
#face_app = FaceAnalysis(name='buffalo_l', root='D:/SnapVault-Backend/AI Models', providers=['CPUExecutionProvider'])
face_app = FaceAnalysis(name='buffalo_l', root='./AI Models', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0)


 
router = APIRouter()   


@router.post("/register", response_model=UserOut)
async def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    email = email.strip().lower()
    try:
        validate_email(email) 
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid email format")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    ext = file.filename.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png']:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, PNG allowed.") 

    profile_pic_name = f"profile_pictures/{uuid.uuid4()}.{ext}"
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE_BYTES_PROFILE_PICTURE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size is 2 MB."
        )

    # Use OpenCV to process the image directly from memory 
    file_bytes = np.asarray(bytearray(file_content), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    faces = face_app.get(img)

    if len(faces) != 1:  

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile picture must contain exactly one face"
        )
    
    # Upload to S3 (Backblaze B2)
    try:
        s3_client.put_object(
            Bucket=BACKBLAZE_BUCKET_NAME,
            Key=profile_pic_name,
            Body=file_content,
            ContentType=file.content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error")
    
    new_embedding = faces[0].embedding

    try:
        # Using a transaction to rollback everything if any step fails
        with db.begin_nested():
            # Creating user
            new_user = User(
                name=name,
                email=email,
                hashed_password=hash_password(password),
                profile_picture=profile_pic_name
            )
            db.add(new_user)
            db.flush()  # flushing to get new_user.id without commit

            # Checking existing faces and try to match
            faces = db.query(Face).all()

            match_found = False
            for face_record in faces:
                stored_embedding = np.array(json.loads(face_record.embedding))
                sim_score = cosine_similarity([new_embedding], [stored_embedding])[0][0]

                if sim_score >= SIMILARITY_THRESHOLD:
                    #Trying to prevent face duplication
                    if face_record.user_id is not None:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="This face is already associated with another user"
                        )
                    
                    count = face_record.embedding_count or 1
                    updated_embedding = (stored_embedding * count + new_embedding) / (count + 1)

                    face_record.embedding = json.dumps(updated_embedding.tolist())
                    face_record.embedding_count = count + 1
                    face_record.user_id = new_user.id
                    
                    match_found = True
                    break

            if not match_found:
                # Creating new face linked to user
                face = Face(
                    embedding=json.dumps(new_embedding.tolist()),
                    embedding_count=1,
                    user_id=new_user.id
                )
                db.add(face)

        db.commit()  # committing transaction if all OK

    except SQLAlchemyError as e:
        db.rollback()
        # Remove uploaded profile picture from S3 on database failure
        try:
            s3_client.delete_object(Bucket=BACKBLAZE_BUCKET_NAME, Key=profile_pic_name)
        except Exception as delete_err:
            print(f"Failed to delete image from S3 after DB error: {delete_err}")

        raise HTTPException(status_code=500, detail="Registration failed, please try again.")


    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    
    user.email = user.email.strip().lower() 

    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    auth_header = request.headers.get("Authorization")
 
    token = auth_header
    if token.startswith("Bearer "):
        token = token.split("Bearer ")[1].strip() 

    if db.query(RevokedToken).filter_by(token=token).first():
        raise HTTPException(status_code=400, detail="Token already revoked")

    db.add(RevokedToken(token=token))
    db.commit()
    return {"message": "Logged out successfully"}
