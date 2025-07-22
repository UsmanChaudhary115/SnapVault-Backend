from email_validator import validate_email, EmailNotValidError
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models.user import User 
from schemas.user import UserLogin, UserOut
from utils.hash import hash_password, verify_password
from utils.jwt import create_access_token
from utils.auth_utils import get_current_user
from utils.supabase_client import (
    create_supabase_user, 
    sign_in_with_password, 
    get_google_oauth_url,
    get_supabase_client,
    verify_supabase_token
)
from passlib.context import CryptContext   
import uuid
import os

router = APIRouter() 

UPLOAD_PROFILE_DIR = "uploads/profile_pictures" 

# Google OAuth routes
@router.get("/supabase_google")
async def google_oauth_login(request: Request):
    """
    Initiate Google OAuth login
    """
    # Get the base URL from the request
    base_url = str(request.base_url).rstrip('/')
    redirect_url = f"{base_url}/auth/supabase_google/callback"
    
    try:
        auth_url = get_google_oauth_url(redirect_url)
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Google OAuth URL: {str(e)}")

@router.get("/supabase_google/callback")
async def google_oauth_callback(
    access_token: str = None,
    refresh_token: str = None,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback
    """
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token is required")
    
    try:
        # Verify the Supabase token and get user data
        user_data = verify_supabase_token(access_token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check if user exists in our database
        user = db.query(User).filter(User.supabase_user_id == user_data["sub"]).first()
        
        if not user:
            # Check by email
            user = db.query(User).filter(User.email == user_data["email"]).first()
            
            if not user:
                # Create new user from Google OAuth data
                user_metadata = user_data.get("user_metadata", {})
                new_user = User(
                    name=user_metadata.get("full_name", user_data["email"].split("@")[0]),
                    email=user_data["email"],
                    supabase_user_id=user_data["sub"],
                    auth_provider="google",
                    profile_picture=user_metadata.get("avatar_url")
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                user = new_user
            else:
                # Update existing user with Supabase ID
                user.supabase_user_id = user_data["sub"]
                user.auth_provider = "google"
                db.commit()
                db.refresh(user)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")

@router.post("/supabase_register", response_model=UserOut)
async def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Simple registration without profile picture (simplified for easier testing)
    """
    email = email.strip().lower()
    try:
        validate_email(email)
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid email format")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    try:
        # Create user in Supabase first
        supabase_response = create_supabase_user(
            email=email,
            password=password,
            user_data={
                "full_name": name
            }
        )
        
        supabase_user_id = None
        if supabase_response.user:
            supabase_user_id = supabase_response.user.id
        
        # Create user in local database
        new_user = User(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            supabase_user_id=supabase_user_id,
            auth_provider="email"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.post("/supabase_register-simple")
async def register_simple(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Simple registration without profile picture (for easier testing)
    """
    email = email.strip().lower()
    try:
        validate_email(email)
    except EmailNotValidError:
        raise HTTPException(status_code=400, detail="Invalid email format")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    try:
        # Create user in Supabase first
        supabase_response = create_supabase_user(
            email=email,
            password=password,
            user_data={
                "full_name": name
            }
        )
        
        supabase_user_id = None
        if supabase_response.user:
            supabase_user_id = supabase_response.user.id
        
        # Create user in local database
        new_user = User(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            supabase_user_id=supabase_user_id,
            auth_provider="email"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.post("/supabase_register-with-photo", response_model=UserOut)
async def register_with_photo(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    file: UploadFile = File(...),  # profile picture
    db: Session = Depends(get_db)
):
    """
    Registration with profile picture upload
    """
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

    profile_pic_name = f"{uuid.uuid4()}.{ext}"
    profile_pic_path = os.path.join(UPLOAD_PROFILE_DIR, profile_pic_name)

    with open(profile_pic_path, "wb") as f:
        f.write(await file.read())

    try:
        # Create user in Supabase first
        supabase_response = create_supabase_user(
            email=email,
            password=password,
            user_data={
                "full_name": name,
                "avatar_url": profile_pic_path
            }
        )
        
        supabase_user_id = None
        if supabase_response.user:
            supabase_user_id = supabase_response.user.id
        
        # Create user in local database
        new_user = User(
            name=name,
            email=email,
            hashed_password=hash_password(password), 
            profile_picture=profile_pic_path,
            supabase_user_id=supabase_user_id,
            auth_provider="email"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
        
    except Exception as e:
        # Clean up uploaded file if user creation fails
        if os.path.exists(profile_pic_path):
            os.remove(profile_pic_path)
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.post("/supabase_login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    user.email = user.email.strip().lower()  # Changed from upper() to lower()

    try:
        # Try Supabase authentication first
        supabase_response = sign_in_with_password(user.email, user.password)
        
        if supabase_response.user:
            # Get user from local database
            db_user = db.query(User).filter(User.email == user.email).first()
            if not db_user:
                raise HTTPException(status_code=401, detail="User not found in local database")
            
            # Update user with Supabase ID if not present
            if not db_user.supabase_user_id and supabase_response.user.id:
                db_user.supabase_user_id = supabase_response.user.id
                db.commit()
                db.refresh(db_user)
            
            return {
                "access_token": supabase_response.session.access_token,
                "token_type": "bearer",
                "user": db_user
            }
    except Exception as supabase_error:
        # Fallback to legacy authentication if Supabase fails
        print(f"Supabase auth failed, trying legacy: {supabase_error}")
        
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user or not verify_password(user.password, db_user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create legacy JWT token
        token = create_access_token({"sub": db_user.email})
        return {"access_token": token, "token_type": "bearer", "user": db_user}

@router.delete("/supabase_delete-account")
def delete_account(
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Delete user account and all associated data using email
    This will delete:
    - User profile and data
    - Profile picture file
    - All uploaded photos by this user
    - Group memberships
    - Supabase user account
    """
    email = email.strip().lower()
    
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # 1. Delete profile picture file if exists
        if user.profile_picture and os.path.exists(user.profile_picture):
            try:
                os.remove(user.profile_picture)
                print(f"Deleted profile picture: {user.profile_picture}")
            except Exception as e:
                print(f"Warning: Could not delete profile picture {user.profile_picture}: {e}")
        
        # 2. Delete all photos uploaded by this user and their files
        from models.photo import Photo
        user_photos = db.query(Photo).filter(Photo.uploader_id == user.id).all()
        for photo in user_photos:
            # Delete photo file
            if photo.file_path and os.path.exists(photo.file_path):
                try:
                    os.remove(photo.file_path)
                    print(f"Deleted photo file: {photo.file_path}")
                except Exception as e:
                    print(f"Warning: Could not delete photo file {photo.file_path}: {e}")
            
            # Delete photo record
            db.delete(photo)
        
        # 3. Delete user's group memberships
        from models.group_member import GroupMember
        user_memberships = db.query(GroupMember).filter(GroupMember.user_id == user.id).all()
        for membership in user_memberships:
            db.delete(membership)
        
        # 4. Handle groups created by this user
        from models.group import Group
        user_groups = db.query(Group).filter(Group.creator_id == user.id).all()
        for group in user_groups:
            # Option 1: Delete the entire group and all its content
            # This is more aggressive but cleaner
            
            # Delete all group photos
            group_photos = db.query(Photo).filter(Photo.group_id == group.id).all()
            for photo in group_photos:
                if photo.file_path and os.path.exists(photo.file_path):
                    try:
                        os.remove(photo.file_path)
                        print(f"Deleted group photo file: {photo.file_path}")
                    except Exception as e:
                        print(f"Warning: Could not delete group photo file {photo.file_path}: {e}")
                db.delete(photo)
            
            # Delete all group memberships
            group_memberships = db.query(GroupMember).filter(GroupMember.group_id == group.id).all()
            for membership in group_memberships:
                db.delete(membership)
            
            # Delete the group
            db.delete(group)
        
        # 5. Delete user's face data
        from models.faces import Face
        user_faces = db.query(Face).filter(Face.user_id == user.id).all()
        for face in user_faces:
            db.delete(face)
        
        # 6. Delete user's photo face associations
        from models.photo_face import PhotoFace
        user_photo_faces = db.query(PhotoFace).filter(PhotoFace.face_id.in_(
            db.query(Face.id).filter(Face.user_id == user.id)
        )).all()
        for photo_face in user_photo_faces:
            db.delete(photo_face)
        
        # 7. Delete from Supabase if user has supabase_user_id
        if user.supabase_user_id:
            try:
                from utils.supabase_client import get_supabase_admin_client
                supabase_admin = get_supabase_admin_client()
                
                # Delete user from Supabase
                supabase_admin.auth.admin.delete_user(user.supabase_user_id)
                print(f"Deleted user from Supabase: {user.supabase_user_id}")
            except Exception as e:
                print(f"Warning: Could not delete user from Supabase: {e}")
                # Continue with local deletion even if Supabase deletion fails
        
        # 8. Finally, delete the user record
        db.delete(user)
        db.commit()
        
        return {
            "message": "Account deleted successfully",
            "deleted_user": {
                "email": email,
                "name": user.name,
                "id": user.id
            },
            "deleted_files": {
                "profile_picture": bool(user.profile_picture),
                "photos_count": len(user_photos),
                "groups_deleted": len(user_groups)
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")

@router.delete("/supabase_delete-account-by-id/{user_id}")
def delete_account_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete user account by ID (requires authentication)
    Only allows users to delete their own account or admin users
    """
    # Find user by ID
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Security check: only allow users to delete their own account
    # (You can modify this to allow admin users as well)
    if current_user.id != user_to_delete.id:
        raise HTTPException(status_code=403, detail="You can only delete your own account")
    
    # Use the same deletion logic as delete_account but with the found user
    email = user_to_delete.email
    
    try:
        # [Same deletion logic as above]
        # 1. Delete profile picture file if exists
        if user_to_delete.profile_picture and os.path.exists(user_to_delete.profile_picture):
            try:
                os.remove(user_to_delete.profile_picture)
                print(f"Deleted profile picture: {user_to_delete.profile_picture}")
            except Exception as e:
                print(f"Warning: Could not delete profile picture: {e}")
        
        # 2. Delete all photos and related data
        from models.photo import Photo
        user_photos = db.query(Photo).filter(Photo.uploader_id == user_to_delete.id).all()
        for photo in user_photos:
            if photo.file_path and os.path.exists(photo.file_path):
                try:
                    os.remove(photo.file_path)
                except Exception as e:
                    print(f"Warning: Could not delete photo file: {e}")
            db.delete(photo)
        
        # 3. Delete memberships and groups (same logic as above)
        from models.group_member import GroupMember
        from models.group import Group
        from models.faces import Face
        from models.photo_face import PhotoFace
        
        # Delete memberships
        user_memberships = db.query(GroupMember).filter(GroupMember.user_id == user_to_delete.id).all()
        for membership in user_memberships:
            db.delete(membership)
        
        # Delete created groups and their content
        user_groups = db.query(Group).filter(Group.creator_id == user_to_delete.id).all()
        for group in user_groups:
            # Delete group photos
            group_photos = db.query(Photo).filter(Photo.group_id == group.id).all()
            for photo in group_photos:
                if photo.file_path and os.path.exists(photo.file_path):
                    try:
                        os.remove(photo.file_path)
                    except Exception as e:
                        print(f"Warning: Could not delete group photo: {e}")
                db.delete(photo)
            
            # Delete group memberships
            group_memberships = db.query(GroupMember).filter(GroupMember.group_id == group.id).all()
            for membership in group_memberships:
                db.delete(membership)
            
            db.delete(group)
        
        # Delete face data
        user_faces = db.query(Face).filter(Face.user_id == user_to_delete.id).all()
        for face in user_faces:
            db.delete(face)
        
        # Delete from Supabase
        if user_to_delete.supabase_user_id:
            try:
                from utils.supabase_client import get_supabase_admin_client
                supabase_admin = get_supabase_admin_client()
                supabase_admin.auth.admin.delete_user(user_to_delete.supabase_user_id)
            except Exception as e:
                print(f"Warning: Could not delete user from Supabase: {e}")
        
        # Delete user record
        db.delete(user_to_delete)
        db.commit()
        
        return {
            "message": "Your account has been deleted successfully",
            "deleted_user": {
                "email": email,
                "name": user_to_delete.name,
                "id": user_to_delete.id
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}") 