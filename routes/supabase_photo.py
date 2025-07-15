"""
Supabase Photo Routes for SnapVault

This module provides photo management endpoints that integrate with Supabase
for metadata storage and synchronization, while using the modular storage system
for file handling and maintaining local database functionality.

All endpoints use the 'supabase_' prefix to distinguish from local routes.

Features:
- Photo upload with Supabase metadata sync
- Advanced photo filtering and search
- Face recognition integration
- Batch operations
- Photo analytics and statistics
- Storage optimization
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.photo import Photo
from models.photo_face import PhotoFace
from models.faces import Face
from models.group_member import GroupMember
from models.user import User
from models.group import Group
from utils.auth_utils import get_current_user
from utils.storage import save_photo, delete_file, get_file_url
from utils.supabase_client import get_supabase_client, get_supabase_admin_client
from schemas.photo import PhotoOut
from typing import List, Optional
import json
from datetime import datetime, timedelta
import uuid
import os

router = APIRouter()


def sync_photo_to_supabase(photo: Photo, operation: str = "create"):
    """
    Sync photo metadata to Supabase
    
    Args:
        photo: Photo object to sync
        operation: Type of operation (create, update, delete)
    """
    try:
        supabase = get_supabase_client()
        
        photo_data = {
            "id": photo.id,
            "group_id": photo.group_id,
            "uploader_id": photo.uploader_id,
            "file_path": photo.file_path,
            "file_url": get_file_url(photo.file_path) if photo.file_path else None,
            "uploaded_at": photo.created_at.isoformat() if photo.created_at else None,
            "file_size": getattr(photo, 'file_size', None),
            "mime_type": getattr(photo, 'mime_type', None),
            "metadata": getattr(photo, 'metadata', {})
        }
        
        if operation == "create":
            supabase.table("photos").insert(photo_data).execute()
        elif operation == "update":
            supabase.table("photos").update(photo_data).eq("id", photo.id).execute()
        elif operation == "delete":
            supabase.table("photos").delete().eq("id", photo.id).execute()
            
    except Exception as e:
        print(f"Warning: Failed to sync photo to Supabase: {e}")


def validate_photo_permissions(user_id: int, group_id: int, required_role_ids: list, db: Session):
    """
    Validate user permissions for photo operations
    
    Args:
        user_id: User ID to check
        group_id: Group ID to check
        required_role_ids: List of role IDs that are allowed
        db: Database session
        
    Returns:
        GroupMember: User's membership if valid
        
    Raises:
        HTTPException: If permission denied
    """
    member = db.query(GroupMember).filter_by(
        user_id=user_id,
        group_id=group_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    
    if member.role_id not in required_role_ids:
        raise HTTPException(status_code=403, detail="You don't have permission for this operation")
    
    return member


@router.post("/supabase_upload", response_model=PhotoOut)
async def upload_photo(
    group_id: int = Form(...),
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    description: Optional[str] = Form(None, description="Photo description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a photo to a group with Supabase synchronization
    
    Args:
        group_id: ID of the group to upload to
        file: Image file to upload
        tags: Optional comma-separated tags
        description: Optional photo description
        
    Returns:
        PhotoOut: Uploaded photo information
        
    Raises:
        HTTPException: 403 if no permission, 400 if invalid file, 500 if upload fails
    """
    try:
        # Validate group membership and permissions
        validate_photo_permissions(
            current_user.id, 
            group_id, 
            [1, 2, 3],  # super-admin, admin, contributor
            db
        )
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only JPEG, PNG, GIF, and WebP images are allowed"
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        content = await file.read()
        file_size = len(content)
        
        if file_size > max_size:
            raise HTTPException(status_code=400, detail="File size cannot exceed 10MB")
        
        # Reset file position for saving
        file.file.seek(0)
        
        # Save file using modular storage
        file_path = await save_photo(file)
        
        # Process tags
        processed_tags = []
        if tags:
            processed_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Create photo metadata
        photo_metadata = {
            "original_filename": file.filename,
            "file_size": file_size,
            "mime_type": file.content_type,
            "tags": processed_tags,
            "description": description.strip() if description else None,
            "upload_ip": None,  # Could be added for audit purposes
            "processing_status": "uploaded"
        }
        
        # Create photo record in local database
        photo = Photo(
            group_id=group_id,
            uploader_id=current_user.id,
            file_path=file_path
        )
        
        # Add metadata if your Photo model supports it
        if hasattr(photo, 'metadata'):
            photo.metadata = json.dumps(photo_metadata)
        if hasattr(photo, 'file_size'):
            photo.file_size = file_size
        if hasattr(photo, 'mime_type'):
            photo.mime_type = file.content_type
        
        db.add(photo)
        db.commit()
        db.refresh(photo)
        
        # Sync to Supabase
        sync_photo_to_supabase(photo, "create")
        
        # Add file URL to response
        photo_dict = photo.__dict__.copy()
        photo_dict['file_url'] = get_file_url(file_path)
        photo_dict['metadata'] = photo_metadata
        
        return photo_dict
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up uploaded file if database operation fails
        if 'file_path' in locals():
            await delete_file(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")


@router.post("/supabase_upload_batch")
async def upload_multiple_photos(
    group_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload multiple photos to a group
    
    Args:
        group_id: ID of the group to upload to
        files: List of image files to upload
        
    Returns:
        dict: Upload results with success and failure counts
        
    Raises:
        HTTPException: 403 if no permission, 400 if invalid request, 500 if upload fails
    """
    try:
        # Validate group membership and permissions
        validate_photo_permissions(
            current_user.id, 
            group_id, 
            [1, 2, 3],  # super-admin, admin, contributor
            db
        )
        
        # Validate batch size
        if len(files) > 20:
            raise HTTPException(status_code=400, detail="Cannot upload more than 20 files at once")
        
        successful_uploads = []
        failed_uploads = []
        
        for file in files:
            try:
                # Validate each file
                allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
                if file.content_type not in allowed_types:
                    failed_uploads.append({
                        "filename": file.filename,
                        "error": "Invalid file type"
                    })
                    continue
                
                # Check file size
                content = await file.read()
                file_size = len(content)
                max_size = 10 * 1024 * 1024  # 10MB
                
                if file_size > max_size:
                    failed_uploads.append({
                        "filename": file.filename,
                        "error": "File size exceeds 10MB"
                    })
                    continue
                
                # Reset file position
                file.file.seek(0)
                
                # Save file
                file_path = await save_photo(file)
                
                # Create photo record
                photo = Photo(
                    group_id=group_id,
                    uploader_id=current_user.id,
                    file_path=file_path
                )
                
                # Add metadata if supported
                if hasattr(photo, 'file_size'):
                    photo.file_size = file_size
                if hasattr(photo, 'mime_type'):
                    photo.mime_type = file.content_type
                if hasattr(photo, 'metadata'):
                    photo.metadata = json.dumps({
                        "original_filename": file.filename,
                        "file_size": file_size,
                        "mime_type": file.content_type,
                        "batch_upload": True
                    })
                
                db.add(photo)
                db.commit()
                db.refresh(photo)
                
                # Sync to Supabase
                sync_photo_to_supabase(photo, "create")
                
                successful_uploads.append({
                    "filename": file.filename,
                    "photo_id": photo.id,
                    "file_url": get_file_url(file_path)
                })
                
            except Exception as e:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": str(e)
                })
                # Clean up file if it was saved but database operation failed
                if 'file_path' in locals():
                    await delete_file(file_path)
        
        return {
            "group_id": group_id,
            "total_files": len(files),
            "successful_uploads": len(successful_uploads),
            "failed_uploads": len(failed_uploads),
            "results": {
                "successful": successful_uploads,
                "failed": failed_uploads
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload photos: {str(e)}")


@router.get("/supabase_group/{group_id}", response_model=List[PhotoOut])
async def get_group_photos(
    group_id: int = Path(..., gt=0),
    limit: int = Query(50, ge=1, le=100, description="Number of photos to return"),
    offset: int = Query(0, ge=0, description="Number of photos to skip"),
    sort_by: str = Query("created_at", description="Sort field: created_at, file_size"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    uploader_id: Optional[int] = Query(None, description="Filter by uploader"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get photos from a group with advanced filtering and pagination
    
    Args:
        group_id: ID of the group
        limit: Maximum number of photos to return
        offset: Number of photos to skip (for pagination)
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        tags: Filter by tags
        uploader_id: Filter by uploader
        date_from: Filter from date
        date_to: Filter to date
        
    Returns:
        List[PhotoOut]: List of photos with metadata
        
    Raises:
        HTTPException: 404 if group not found, 403 if no permission, 500 if query fails
    """
    try:
        # Validate group exists
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Validate group membership and permissions
        validate_photo_permissions(
            current_user.id, 
            group_id, 
            [1, 2, 3, 4],  # All roles except restricted viewer
            db
        )
        
        # Build query
        query = db.query(Photo).filter(Photo.group_id == group_id)
        
        # Apply filters
        if uploader_id:
            query = query.filter(Photo.uploader_id == uploader_id)
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(Photo.created_at >= from_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD")
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(Photo.created_at < to_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")
        
        # Apply sorting
        if sort_by == "created_at":
            if sort_order == "asc":
                query = query.order_by(Photo.created_at.asc())
            else:
                query = query.order_by(Photo.created_at.desc())
        elif sort_by == "file_size" and hasattr(Photo, 'file_size'):
            if sort_order == "asc":
                query = query.order_by(Photo.file_size.asc())
            else:
                query = query.order_by(Photo.file_size.desc())
        else:
            # Default sorting
            query = query.order_by(Photo.created_at.desc())
        
        # Apply pagination
        photos = query.offset(offset).limit(limit).all()
        
        # Enhance photos with additional data
        result = []
        for photo in photos:
            photo_dict = photo.__dict__.copy()
            photo_dict['file_url'] = get_file_url(photo.file_path)
            
            # Add uploader info
            uploader = db.query(User).filter(User.id == photo.uploader_id).first()
            photo_dict['uploader_name'] = uploader.name if uploader else "Unknown"
            
            # Parse metadata if available
            if hasattr(photo, 'metadata') and photo.metadata:
                try:
                    photo_dict['metadata'] = json.loads(photo.metadata)
                except json.JSONDecodeError:
                    photo_dict['metadata'] = {}
            
            result.append(photo_dict)
        
        # Filter by tags if requested (done after query for simplicity)
        if tags:
            requested_tags = [tag.strip().lower() for tag in tags.split(',')]
            filtered_result = []
            for photo in result:
                photo_tags = photo.get('metadata', {}).get('tags', [])
                photo_tags_lower = [tag.lower() for tag in photo_tags]
                if any(tag in photo_tags_lower for tag in requested_tags):
                    filtered_result.append(photo)
            result = filtered_result
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get group photos: {str(e)}")


@router.get("/supabase_my/photos/all", response_model=List[PhotoOut])
async def get_my_photos_all_groups(
    limit: int = Query(50, ge=1, le=100, description="Number of photos to return"),
    offset: int = Query(0, ge=0, description="Number of photos to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all photos where the current user appears (across all groups they're in)
    
    Args:
        limit: Maximum number of photos to return
        offset: Number of photos to skip
        
    Returns:
        List[PhotoOut]: List of photos containing the user
        
    Raises:
        HTTPException: 404 if no face found, 500 if query fails
    """
    try:
        # Find user's face
        user_face = db.query(Face).filter(Face.user_id == current_user.id).first()
        if not user_face:
            return []  # Return empty list instead of error if no face found
        
        # Get photos where user appears
        photo_faces = db.query(PhotoFace).filter(PhotoFace.face_id == user_face.id).all()
        photo_ids = [pf.photo_id for pf in photo_faces]
        
        if not photo_ids:
            return []
        
        # Get user's group memberships to filter accessible photos
        user_groups = db.query(GroupMember).filter(GroupMember.user_id == current_user.id).all()
        accessible_group_ids = [gm.group_id for gm in user_groups]
        
        # Query photos
        photos = db.query(Photo).filter(
            Photo.id.in_(photo_ids),
            Photo.group_id.in_(accessible_group_ids)
        ).order_by(Photo.created_at.desc()).offset(offset).limit(limit).all()
        
        # Enhance with additional data
        result = []
        for photo in photos:
            photo_dict = photo.__dict__.copy()
            photo_dict['file_url'] = get_file_url(photo.file_path)
            
            # Add group info
            group = db.query(Group).filter(Group.id == photo.group_id).first()
            photo_dict['group_name'] = group.name if group else "Unknown"
            
            # Add uploader info
            uploader = db.query(User).filter(User.id == photo.uploader_id).first()
            photo_dict['uploader_name'] = uploader.name if uploader else "Unknown"
            
            result.append(photo_dict)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user photos: {str(e)}")


@router.get("/supabase_my/photos/{group_id}", response_model=List[PhotoOut])
async def get_my_photos_in_group(
    group_id: int,
    limit: int = Query(50, ge=1, le=100, description="Number of photos to return"),
    offset: int = Query(0, ge=0, description="Number of photos to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get photos where the current user appears in a specific group
    
    Args:
        group_id: ID of the group
        limit: Maximum number of photos to return
        offset: Number of photos to skip
        
    Returns:
        List[PhotoOut]: List of photos containing the user in the specified group
        
    Raises:
        HTTPException: 404 if group/face not found, 403 if not member, 500 if query fails
    """
    try:
        # Validate group exists and user is a member
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        membership = db.query(GroupMember).filter_by(
            user_id=current_user.id,
            group_id=group_id
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this group")
        
        # Find user's face
        user_face = db.query(Face).filter(Face.user_id == current_user.id).first()
        if not user_face:
            return []
        
        # Get photo IDs where user appears
        photo_faces = db.query(PhotoFace).filter(PhotoFace.face_id == user_face.id).all()
        photo_ids = [pf.photo_id for pf in photo_faces]
        
        if not photo_ids:
            return []
        
        # Get photos in the specific group
        photos = db.query(Photo).filter(
            Photo.group_id == group_id,
            Photo.id.in_(photo_ids)
        ).order_by(Photo.created_at.desc()).offset(offset).limit(limit).all()
        
        # Enhance with additional data
        result = []
        for photo in photos:
            photo_dict = photo.__dict__.copy()
            photo_dict['file_url'] = get_file_url(photo.file_path)
            photo_dict['group_name'] = group.name
            
            # Add uploader info
            uploader = db.query(User).filter(User.id == photo.uploader_id).first()
            photo_dict['uploader_name'] = uploader.name if uploader else "Unknown"
            
            result.append(photo_dict)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user photos in group: {str(e)}")


@router.get("/supabase_photo/{photo_id}", response_model=PhotoOut)
async def get_photo_details(
    photo_id: int = Path(..., gt=0),
    include_faces: bool = Query(False, description="Include face detection data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific photo
    
    Args:
        photo_id: ID of the photo
        include_faces: Whether to include face detection data
        
    Returns:
        PhotoOut: Detailed photo information
        
    Raises:
        HTTPException: 404 if photo not found, 403 if no permission, 500 if query fails
    """
    try:
        # Find photo
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        # Check if user has access to this photo (member of the group)
        membership = db.query(GroupMember).filter_by(
            user_id=current_user.id,
            group_id=photo.group_id
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="You don't have access to this photo")
        
        # Build detailed response
        photo_dict = photo.__dict__.copy()
        photo_dict['file_url'] = get_file_url(photo.file_path)
        
        # Add group info
        group = db.query(Group).filter(Group.id == photo.group_id).first()
        photo_dict['group'] = {
            "id": group.id,
            "name": group.name
        } if group else None
        
        # Add uploader info
        uploader = db.query(User).filter(User.id == photo.uploader_id).first()
        photo_dict['uploader'] = {
            "id": uploader.id,
            "name": uploader.name
        } if uploader else None
        
        # Parse metadata
        if hasattr(photo, 'metadata') and photo.metadata:
            try:
                photo_dict['metadata'] = json.loads(photo.metadata)
            except json.JSONDecodeError:
                photo_dict['metadata'] = {}
        
        # Include face data if requested
        if include_faces:
            photo_faces = db.query(PhotoFace, Face, User).join(
                Face, PhotoFace.face_id == Face.id
            ).join(
                User, Face.user_id == User.id
            ).filter(PhotoFace.photo_id == photo_id).all()
            
            faces_data = []
            for photo_face, face, user in photo_faces:
                faces_data.append({
                    "user_id": user.id,
                    "user_name": user.name,
                    "confidence": getattr(photo_face, 'confidence', None),
                    "bounding_box": getattr(photo_face, 'bounding_box', None)
                })
            
            photo_dict['detected_faces'] = faces_data
        
        return photo_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get photo details: {str(e)}")


@router.delete("/supabase_photo/{photo_id}")
async def delete_photo(
    photo_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a photo (uploader or group admin/owner only)
    
    Args:
        photo_id: ID of the photo to delete
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if photo not found, 403 if no permission, 500 if deletion fails
    """
    try:
        # Find photo
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        # Check permissions (uploader or group admin/owner)
        membership = db.query(GroupMember).filter_by(
            user_id=current_user.id,
            group_id=photo.group_id
        ).first()
        
        if not membership:
            raise HTTPException(status_code=403, detail="You don't have access to this photo")
        
        # Allow deletion if user is uploader or admin/owner
        if photo.uploader_id != current_user.id and membership.role_id not in [1, 2]:
            raise HTTPException(status_code=403, detail="Only the uploader or group admin can delete this photo")
        
        # Delete file
        try:
            await delete_file(photo.file_path)
        except Exception as e:
            print(f"Warning: Could not delete photo file {photo.file_path}: {e}")
        
        # Delete face associations
        photo_faces = db.query(PhotoFace).filter(PhotoFace.photo_id == photo_id).all()
        for photo_face in photo_faces:
            db.delete(photo_face)
        
        # Sync deletion to Supabase before deleting from local DB
        sync_photo_to_supabase(photo, "delete")
        
        # Delete photo record
        db.delete(photo)
        db.commit()
        
        return {
            "message": "Photo deleted successfully",
            "photo_id": photo_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete photo: {str(e)}")


@router.get("/supabase_analytics/group/{group_id}")
async def get_photo_analytics(
    group_id: int = Path(..., gt=0),
    days: int = Query(30, ge=1, le=365, description="Number of days for analytics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get photo analytics for a group
    
    Args:
        group_id: ID of the group
        days: Number of days to include in analytics
        
    Returns:
        dict: Photo analytics data
        
    Raises:
        HTTPException: 404 if group not found, 403 if no permission, 500 if query fails
    """
    try:
        # Validate group and permissions
        membership = validate_photo_permissions(
            current_user.id, 
            group_id, 
            [1, 2],  # Only admin and owner
            db
        )
        
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Basic statistics
        total_photos = db.query(Photo).filter(Photo.group_id == group_id).count()
        recent_photos = db.query(Photo).filter(
            Photo.group_id == group_id,
            Photo.created_at >= start_date
        ).count()
        
        # Storage usage
        group_photos = db.query(Photo).filter(Photo.group_id == group_id).all()
        total_storage = 0
        for photo in group_photos:
            try:
                if photo.file_path and os.path.exists(photo.file_path):
                    total_storage += os.path.getsize(photo.file_path)
            except Exception:
                pass
        
        # Top uploaders
        top_uploaders = db.query(
            User.name,
            func.count(Photo.id).label('photo_count')
        ).join(Photo, User.id == Photo.uploader_id)\
         .filter(Photo.group_id == group_id)\
         .group_by(User.id, User.name)\
         .order_by(func.count(Photo.id).desc())\
         .limit(5).all()
        
        # Photos by day (last 7 days)
        daily_stats = []
        for i in range(7):
            day = end_date - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_count = db.query(Photo).filter(
                Photo.group_id == group_id,
                Photo.created_at >= day_start,
                Photo.created_at < day_end
            ).count()
            
            daily_stats.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "photo_count": day_count
            })
        
        analytics = {
            "group_id": group_id,
            "period_days": days,
            "summary": {
                "total_photos": total_photos,
                "recent_photos": recent_photos,
                "total_storage_bytes": total_storage,
                "storage_mb": round(total_storage / (1024 * 1024), 2),
                "photos_per_day": round(recent_photos / days, 2) if days > 0 else 0
            },
            "top_uploaders": [
                {"name": name, "photo_count": count} 
                for name, count in top_uploaders
            ],
            "daily_uploads": daily_stats
        }
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get photo analytics: {str(e)}")


@router.post("/supabase_batch_tag")
async def batch_tag_photos(
    photo_ids: List[int],
    tags: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add tags to multiple photos
    
    Args:
        photo_ids: List of photo IDs to tag
        tags: List of tags to add
        
    Returns:
        dict: Operation results
        
    Raises:
        HTTPException: 400 if invalid input, 403 if no permission, 500 if operation fails
    """
    try:
        if not photo_ids or not tags:
            raise HTTPException(status_code=400, detail="Photo IDs and tags are required")
        
        if len(photo_ids) > 50:
            raise HTTPException(status_code=400, detail="Cannot tag more than 50 photos at once")
        
        successful_updates = 0
        failed_updates = []
        
        for photo_id in photo_ids:
            try:
                # Find photo
                photo = db.query(Photo).filter(Photo.id == photo_id).first()
                if not photo:
                    failed_updates.append({"photo_id": photo_id, "error": "Photo not found"})
                    continue
                
                # Check permissions
                membership = db.query(GroupMember).filter_by(
                    user_id=current_user.id,
                    group_id=photo.group_id
                ).first()
                
                if not membership or membership.role_id not in [1, 2, 3]:
                    failed_updates.append({"photo_id": photo_id, "error": "No permission"})
                    continue
                
                # Update tags if metadata field exists
                if hasattr(photo, 'metadata'):
                    try:
                        metadata = json.loads(photo.metadata) if photo.metadata else {}
                    except json.JSONDecodeError:
                        metadata = {}
                    
                    existing_tags = metadata.get('tags', [])
                    new_tags = list(set(existing_tags + tags))  # Merge and deduplicate
                    metadata['tags'] = new_tags
                    
                    photo.metadata = json.dumps(metadata)
                    db.commit()
                    
                    # Sync to Supabase
                    sync_photo_to_supabase(photo, "update")
                    
                    successful_updates += 1
                else:
                    failed_updates.append({"photo_id": photo_id, "error": "Metadata not supported"})
                
            except Exception as e:
                failed_updates.append({"photo_id": photo_id, "error": str(e)})
        
        return {
            "total_photos": len(photo_ids),
            "successful_updates": successful_updates,
            "failed_updates": len(failed_updates),
            "tags_added": tags,
            "failures": failed_updates
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to batch tag photos: {str(e)}") 