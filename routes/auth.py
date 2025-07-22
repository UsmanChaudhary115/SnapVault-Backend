from email_validator import validate_email, EmailNotValidError
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models.faces import Face
from models.user import User
from models.revoked_token import RevokedToken
from schemas.user import UserCreate, UserLogin, UserOut, PasswordUpdate
from utils.hash import hash_password, verify_password
from utils.jwt import create_access_token
from utils.auth_utils import get_current_user
from passlib.context import CryptContext   
from sqlalchemy.exc import SQLAlchemyError
#from insightface.app import FaceAnalysis
import cv2, uuid, json, os
import numpy as np  
from sklearn.metrics.pairwise import cosine_similarity 
from insightface.app import FaceAnalysis

# Setup insightface model (CPU only)
face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0)
 
# app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
# app.prepare(ctx_id=0)

router = APIRouter() 

UPLOAD_PROFILE_DIR = "uploads/profile_pictures" 
THRESHOLD = 0.6
# @router.post("/register", response_model=UserOut)
# async def register(
#     name: str = Form(...),
#     email: str = Form(...),
#     password: str = Form(...),
#     file: UploadFile = File(...),  # profile picture
#     db: Session = Depends(get_db)
# ):
#     email = email.strip().upper() 
#     try:
#         validate_email(email)
#     except EmailNotValidError:
#         raise HTTPException(status_code=400, detail="Invalid email format")

#     if db.query(User).filter(User.email == email).first():
#         raise HTTPException(status_code=400, detail="Email already exists")

#     ext = file.filename.split('.')[-1].lower()
#     if ext not in ['jpg', 'jpeg', 'png']:
#         raise HTTPException(status_code=400, detail="Only JPG, JPEG, PNG allowed.")

#     profile_pic_name = f"{uuid.uuid4()}.{ext}"
#     profile_pic_path = os.path.join(UPLOAD_PROFILE_DIR, profile_pic_name)

#     with open(profile_pic_path, "wb") as f:
#         f.write(await file.read())

#     new_user = User(
#         name=name,
#         email=email,
#         hashed_password=hash_password(password), 
#         profile_picture=profile_pic_path
#     )
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return new_user

@router.post("/register", response_model=UserOut)
async def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    email = email.strip().upper()
    try:
        validate_email(email)
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid email format")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    ext = file.filename.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png']:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, PNG allowed.")

    profile_pic_name = f"{uuid.uuid4()}.{ext}"
    profile_pic_path = os.path.join(UPLOAD_PROFILE_DIR, profile_pic_name)

    # Save uploaded file to disk
    with open(profile_pic_path, "wb") as f:
        f.write(await file.read())

    # Read image and detect faces
    img = cv2.imread(profile_pic_path)
    faces = face_app.get(img)

    if len(faces) != 1:
        # Delete saved profile pic, rollback user creation if any, and raise error
        os.remove(profile_pic_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile picture must contain exactly one face. Detected: {len(faces)}"
        )

    new_embedding = faces[0].embedding

    try:
        # Use a transaction to rollback everything if any step fails
        with db.begin_nested():
            # Create user
            new_user = User(
                name=name,
                email=email,
                hashed_password=hash_password(password),
                profile_picture=profile_pic_path
            )
            db.add(new_user)
            db.flush()  # flush to get new_user.id without commit

            # Check orphan faces and try to match
            orphan_faces = db.query(Face).filter(Face.user_id == None).all()

            match_found = False
            for face_record in orphan_faces:
                stored_embedding = np.array(json.loads(face_record.embedding))
                sim_score = cosine_similarity([new_embedding], [stored_embedding])[0][0]

                if sim_score >= THRESHOLD:
                    count = face_record.embedding_count or 1
                    updated_embedding = (stored_embedding * count + new_embedding) / (count + 1)

                    face_record.embedding = json.dumps(updated_embedding.tolist())
                    face_record.embedding_count = count + 1
                    face_record.user_id = new_user.id
                    match_found = True
                    break

            if not match_found:
                # Create new face linked to user
                face = Face(
                    embedding=json.dumps(new_embedding.tolist()),
                    embedding_count=1,
                    user_id=new_user.id
                )
                db.add(face)

        db.commit()  # commit transaction if all OK

    except SQLAlchemyError as e:
        db.rollback()
        # Remove saved profile picture on failure
        if os.path.exists(profile_pic_path):
            os.remove(profile_pic_path)
        raise HTTPException(status_code=500, detail="Registration failed, please try again.")

    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    
    user.email = user.email.strip().upper() 

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


 
    if db.query(RevokedToken).filter_by(token=auth_header).first():
        raise HTTPException(status_code=400, detail="Token already revoked")
 
    db.add(RevokedToken(token=auth_header))
    db.commit()
    return {"message": "Logged out successfully"}