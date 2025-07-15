"""
Supabase User Routes for SnapVault

This module provides user management endpoints that integrate with Supabase
for data storage and authentication, while using the modular storage system
for file handling.

All endpoints use the 'supabase_' prefix to distinguish from local routes.

Features:
- Profile management with Supabase integration
- Profile picture handling with modular storage
- Email validation and updates
- User deletion with cleanup
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.user import UserOut, UpdateUser
from utils.auth_utils import get_current_user
from utils.storage import save_profile_picture, delete_file, get_file_url
from utils.supabase_client import get_supabase_client, get_supabase_admin_client
from email_validator import validate_email, EmailNotValidError
from passlib.context import CryptContext
from typing import Optional
import json

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/supabase_profile", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile information
    
    Returns:
        UserOut: Current user's profile data
        
    Raises:
        HTTPException: 401 if user not authenticated
    """
    try:
        # Get additional user data from Supabase if available
        if current_user.supabase_user_id:
            supabase = get_supabase_client()
            try:
                # Get user metadata from Supabase
                supabase_user = supabase.auth.admin.get_user_by_id(current_user.supabase_user_id)
                if supabase_user.user:
                    # Merge any additional metadata
                    user_metadata = supabase_user.user.user_metadata or {}
                    # Update profile picture URL if it exists in metadata
                    if 'avatar_url' in user_metadata and not current_user.profile_picture:
                        current_user.profile_picture = user_metadata['avatar_url']
            except Exception as e:
                # Continue with local data if Supabase call fails
                print(f"Warning: Could not fetch Supabase user data: {e}")
        
        return current_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@router.put("/supabase_bio/{updated_bio}", response_model=UserOut)
async def update_user_bio(
    updated_bio: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Update user's bio/description
    
    Args:
        updated_bio: New bio text
        
    Returns:
        UserOut: Updated user profile
        
    Raises:
        HTTPException: 400 if bio is too long, 500 if update fails
    """
    try:
        # Validate bio length
        if len(updated_bio) > 500:
            raise HTTPException(status_code=400, detail="Bio cannot exceed 500 characters")
        
        # Update local database
        current_user.bio = updated_bio
        db.commit()
        db.refresh(current_user)
        
        # Update Supabase user metadata if user has Supabase ID
        if current_user.supabase_user_id:
            try:
                supabase = get_supabase_admin_client()
                supabase.auth.admin.update_user_by_id(
                    current_user.supabase_user_id,
                    {"user_metadata": {"bio": updated_bio}}
                )
            except Exception as e:
                print(f"Warning: Could not update Supabase user metadata: {e}")
        
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update bio: {str(e)}")


@router.put("/supabase_name/{name}", response_model=UserOut)
async def update_user_name(
    name: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Update user's display name
    
    Args:
        name: New display name
        
    Returns:
        UserOut: Updated user profile
        
    Raises:
        HTTPException: 400 if name is invalid, 500 if update fails
    """
    try:
        # Validate name
        name = name.strip()
        if not name or len(name) < 2:
            raise HTTPException(status_code=400, detail="Name must be at least 2 characters long")
        if len(name) > 100:
            raise HTTPException(status_code=400, detail="Name cannot exceed 100 characters")
        
        # Update local database
        current_user.name = name
        db.commit()
        db.refresh(current_user)
        
        # Update Supabase user metadata if user has Supabase ID
        if current_user.supabase_user_id:
            try:
                supabase = get_supabase_admin_client()
                supabase.auth.admin.update_user_by_id(
                    current_user.supabase_user_id,
                    {"user_metadata": {"full_name": name}}
                )
            except Exception as e:
                print(f"Warning: Could not update Supabase user metadata: {e}")
        
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update name: {str(e)}")


@router.put("/supabase_profile_picture", response_model=UserOut)
async def update_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user's profile picture
    
    Args:
        file: New profile picture file
        
    Returns:
        UserOut: Updated user profile with new picture URL
        
    Raises:
        HTTPException: 400 if file type invalid, 500 if upload fails
    """
    try:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only JPEG, PNG, GIF, and WebP images are allowed"
            )
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > max_size:
            raise HTTPException(status_code=400, detail="File size cannot exceed 5MB")
        
        # Reset file position for saving
        file.file.seek(0)
        
        # Delete old profile picture if exists
        old_file_path = None
        if current_user.profile_picture:
            old_file_path = current_user.profile_picture
            print(f"🗑️  Attempting to delete old profile picture: {old_file_path}")
            
            try:
                deletion_success = await delete_file(old_file_path)
                if deletion_success:
                    print(f"✅ Successfully deleted old profile picture: {old_file_path}")
                else:
                    print(f"⚠️  Failed to delete old profile picture: {old_file_path} (file may not exist)")
            except Exception as e:
                print(f"❌ Error deleting old profile picture {old_file_path}: {e}")
                # Continue with upload even if deletion fails
        
        # Save new profile picture using modular storage
        print(f"📁 Saving new profile picture...")
        file_path = await save_profile_picture(file)
        print(f"✅ New profile picture saved: {file_path}")
        
        # Update local database
        current_user.profile_picture = file_path
        db.commit()
        db.refresh(current_user)
        
        # Update Supabase user metadata with new avatar URL
        if current_user.supabase_user_id:
            try:
                supabase = get_supabase_admin_client()
                avatar_url = get_file_url(file_path)
                supabase.auth.admin.update_user_by_id(
                    current_user.supabase_user_id,
                    {"user_metadata": {"avatar_url": avatar_url}}
                )
            except Exception as e:
                print(f"Warning: Could not update Supabase user avatar: {e}")
        
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Clean up uploaded file if database update fails
        if 'file_path' in locals():
            await delete_file(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to update profile picture: {str(e)}")


@router.put("/supabase_email", response_model=UserOut)
async def update_user_email(
    updated_user: UpdateUser, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Update user's email address
    
    Args:
        updated_user: UpdateUser schema with new email and password confirmation
        
    Returns:
        UserOut: Updated user profile
        
    Raises:
        HTTPException: 400 if validation fails, 409 if email exists, 500 if update fails
    """
    try:
        # Validate email format
        if not updated_user.email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        try:
            validate_email(updated_user.email)
        except EmailNotValidError:
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Normalize email
        new_email = updated_user.email.strip().lower()
        
        # Check if email is different
        if new_email == current_user.email.lower():
            raise HTTPException(status_code=400, detail="New email cannot be the same as current email")
        
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == new_email).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="Email already exists")
        
        # Verify current password
        if not pwd_context.verify(updated_user.password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect password")
        
        # Update email in Supabase first
        if current_user.supabase_user_id:
            try:
                supabase = get_supabase_admin_client()
                supabase.auth.admin.update_user_by_id(
                    current_user.supabase_user_id,
                    {"email": new_email}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to update email in Supabase: {str(e)}")
        
        # Update local database
        current_user.email = new_email
        db.commit()
        db.refresh(current_user)
        
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update email: {str(e)}")


@router.delete("/supabase_delete", status_code=status.HTTP_200_OK)
async def delete_user_account(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Delete current user's account and all associated data
    
    This will delete:
    - User profile and local data
    - Profile picture file
    - All uploaded photos by this user
    - Group memberships
    - Groups created by user (and all their content)
    - Supabase user account
    
    Returns:
        dict: Confirmation message with deletion summary
        
    Raises:
        HTTPException: 500 if deletion fails
    """
    try:
        user_id = current_user.id
        user_email = current_user.email
        user_name = current_user.name
        
        # Delete profile picture file if exists
        deleted_files = {"profile_picture": False, "photos_count": 0, "groups_deleted": 0}
        
        if current_user.profile_picture:
            try:
                await delete_file(current_user.profile_picture)
                deleted_files["profile_picture"] = True
            except Exception as e:
                print(f"Warning: Could not delete profile picture: {e}")
        
        # Delete all photos uploaded by this user and their files
        from models.photo import Photo
        user_photos = db.query(Photo).filter(Photo.uploader_id == user_id).all()
        for photo in user_photos:
            try:
                await delete_file(photo.file_path)
            except Exception as e:
                print(f"Warning: Could not delete photo file {photo.file_path}: {e}")
            db.delete(photo)
        deleted_files["photos_count"] = len(user_photos)
        
        # Delete user's group memberships
        from models.group_member import GroupMember
        user_memberships = db.query(GroupMember).filter(GroupMember.user_id == user_id).all()
        for membership in user_memberships:
            db.delete(membership)
        
        # Handle groups created by this user
        from models.group import Group
        user_groups = db.query(Group).filter(Group.creator_id == user_id).all()
        for group in user_groups:
            # Delete all group photos
            group_photos = db.query(Photo).filter(Photo.group_id == group.id).all()
            for photo in group_photos:
                try:
                    await delete_file(photo.file_path)
                except Exception as e:
                    print(f"Warning: Could not delete group photo: {e}")
                db.delete(photo)
            
            # Delete all group memberships
            group_memberships = db.query(GroupMember).filter(GroupMember.group_id == group.id).all()
            for membership in group_memberships:
                db.delete(membership)
            
            # Delete the group
            db.delete(group)
        deleted_files["groups_deleted"] = len(user_groups)
        
        # Delete user's face data
        from models.faces import Face
        user_faces = db.query(Face).filter(Face.user_id == user_id).all()
        for face in user_faces:
            db.delete(face)
        
        # Delete user's photo face associations
        from models.photo_face import PhotoFace
        user_photo_faces = db.query(PhotoFace).filter(PhotoFace.face_id.in_(
            db.query(Face.id).filter(Face.user_id == user_id)
        )).all()
        for photo_face in user_photo_faces:
            db.delete(photo_face)
        
        # Delete from Supabase if user has supabase_user_id
        if current_user.supabase_user_id:
            try:
                supabase = get_supabase_admin_client()
                supabase.auth.admin.delete_user(current_user.supabase_user_id)
                print(f"Deleted user from Supabase: {current_user.supabase_user_id}")
            except Exception as e:
                print(f"Warning: Could not delete user from Supabase: {e}")
        
        # Finally, delete the user record
        db.delete(current_user)
        db.commit()
        
        return {
            "message": "Account deleted successfully",
            "deleted_user": {
                "id": user_id,
                "email": user_email,
                "name": user_name
            },
            "deleted_files": deleted_files
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")


@router.get("/supabase_storage_stats")
async def get_user_storage_stats(current_user: User = Depends(get_current_user)):
    """
    Get storage statistics for the current user
    
    Returns:
        dict: Storage usage statistics
        
    Raises:
        HTTPException: 500 if stats calculation fails
    """
    try:
        from utils.storage import StorageStats
        
        # Calculate user's storage usage
        storage_stats = {
            "user_id": current_user.id,
            "profile_picture_size": 0,
            "total_photos": 0,
            "total_storage_bytes": 0,
            "storage_limit_bytes": 100 * 1024 * 1024,  # 100MB default limit
        }
        
        # Get profile picture size
        if current_user.profile_picture:
            try:
                import os
                if os.path.exists(current_user.profile_picture):
                    storage_stats["profile_picture_size"] = os.path.getsize(current_user.profile_picture)
            except Exception:
                pass
        
        # Calculate total photos and storage
        from models.photo import Photo
        from database import get_db
        
        with next(get_db()) as db:
            user_photos = db.query(Photo).filter(Photo.uploader_id == current_user.id).all()
            storage_stats["total_photos"] = len(user_photos)
            
            total_size = storage_stats["profile_picture_size"]
            for photo in user_photos:
                try:
                    import os
                    if photo.file_path and os.path.exists(photo.file_path):
                        total_size += os.path.getsize(photo.file_path)
                except Exception:
                    pass
            
            storage_stats["total_storage_bytes"] = total_size
            storage_stats["storage_used_percentage"] = (total_size / storage_stats["storage_limit_bytes"]) * 100
        
        return storage_stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage stats: {str(e)}")


@router.get("/supabase_debug_files")
async def debug_user_files(current_user: User = Depends(get_current_user)):
    """
    Debug endpoint to check user's file status
    
    Returns:
        dict: File status information for debugging
    """
    try:
        import os
        
        debug_info = {
            "user_id": current_user.id,
            "profile_picture_in_db": current_user.profile_picture,
            "file_checks": {}
        }
        
        # Check if profile picture file exists
        if current_user.profile_picture:
            file_path = current_user.profile_picture
            normalized_path = os.path.normpath(file_path)
            
            debug_info["file_checks"]["profile_picture"] = {
                "path": file_path,
                "normalized_path": normalized_path,
                "exists": os.path.exists(normalized_path),
                "is_file": os.path.isfile(normalized_path) if os.path.exists(normalized_path) else False,
                "size": os.path.getsize(normalized_path) if os.path.exists(normalized_path) else 0
            }
        else:
            debug_info["file_checks"]["profile_picture"] = "No profile picture set"
        
        # List all files in profile pictures directory
        profile_dir = "uploads/profile_pictures"
        if os.path.exists(profile_dir):
            files = []
            for file in os.listdir(profile_dir):
                file_path = os.path.join(profile_dir, file)
                if os.path.isfile(file_path):
                    files.append({
                        "name": file,
                        "path": file_path,
                        "size": os.path.getsize(file_path)
                    })
            debug_info["profile_pictures_directory"] = {
                "path": profile_dir,
                "exists": True,
                "files": files,
                "total_files": len(files)
            }
        else:
            debug_info["profile_pictures_directory"] = {
                "path": profile_dir,
                "exists": False
            }
        
        return debug_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")


@router.get("/supabase_user_activity")
async def get_user_activity(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent user activity
    
    Args:
        limit: Maximum number of activities to return (default: 10, max: 50)
        
    Returns:
        dict: Recent user activities
        
    Raises:
        HTTPException: 400 if limit invalid, 500 if query fails
    """
    try:
        # Validate limit
        if limit < 1 or limit > 50:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")
        
        # Get user's recent activities
        activities = []
        
        # Recent photos uploaded
        from models.photo import Photo
        recent_photos = db.query(Photo).filter(
            Photo.uploader_id == current_user.id
        ).order_by(Photo.created_at.desc()).limit(limit).all()
        
        for photo in recent_photos:
            activities.append({
                "type": "photo_upload",
                "timestamp": photo.created_at,
                "details": {
                    "photo_id": photo.id,
                    "group_id": photo.group_id
                }
            })
        
        # Recent group joins
        from models.group_member import GroupMember
        recent_memberships = db.query(GroupMember).filter(
            GroupMember.user_id == current_user.id
        ).order_by(GroupMember.id.desc()).limit(limit).all()
        
        for membership in recent_memberships:
            activities.append({
                "type": "group_join",
                "timestamp": None,  # Add timestamp to GroupMember model if needed
                "details": {
                    "group_id": membership.group_id,
                    "role_id": membership.role_id
                }
            })
        
        # Sort activities by timestamp (most recent first)
        activities = sorted(
            [activity for activity in activities if activity["timestamp"]],
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
        
        return {
            "user_id": current_user.id,
            "activities": activities,
            "total_count": len(activities)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user activity: {str(e)}") 