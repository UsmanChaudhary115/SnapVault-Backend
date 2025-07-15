"""
Supabase Group Routes for SnapVault

This module provides group management endpoints that integrate with Supabase
for data storage and synchronization, while maintaining local database
functionality and using the modular storage system.

All endpoints use the 'supabase_' prefix to distinguish from local routes.

Features:
- Group creation and management with Supabase sync
- Member management with role-based permissions
- Invite code system
- Group statistics and analytics
- Storage management per group
"""

import random
import string
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.group import Group
from models.groupRoles import GroupRole
from models.group_member import GroupMember
from models.user import User
from schemas.group import GroupCreate, GroupJoin, GroupOut, GroupUpdate
from utils.auth_utils import get_current_user
from utils.supabase_client import get_supabase_client, get_supabase_admin_client
from utils.storage import StorageStats
from typing import Optional, List
import json
from datetime import datetime

router = APIRouter()


def generate_invite_code(length=6):
    """Generate a random invite code for groups"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def sync_group_to_supabase(group: Group, operation: str = "create"):
    """
    Sync group data to Supabase
    
    Args:
        group: Group object to sync
        operation: Type of operation (create, update, delete)
    """
    try:
        supabase = get_supabase_client()
        
        group_data = {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "creator_id": group.creator_id,
            "invite_code": group.invite_code,
            "created_at": group.created_at.isoformat() if group.created_at else None
        }
        
        if operation == "create":
            supabase.table("groups").insert(group_data).execute()
        elif operation == "update":
            supabase.table("groups").update(group_data).eq("id", group.id).execute()
        elif operation == "delete":
            supabase.table("groups").delete().eq("id", group.id).execute()
            
    except Exception as e:
        print(f"Warning: Failed to sync group to Supabase: {e}")


def sync_membership_to_supabase(membership: GroupMember, operation: str = "create"):
    """
    Sync group membership to Supabase
    
    Args:
        membership: GroupMember object to sync
        operation: Type of operation (create, update, delete)
    """
    try:
        supabase = get_supabase_client()
        
        membership_data = {
            "user_id": membership.user_id,
            "group_id": membership.group_id,
            "role_id": membership.role_id
        }
        
        if operation == "create":
            supabase.table("group_members").insert(membership_data).execute()
        elif operation == "update":
            supabase.table("group_members").update(membership_data).eq("user_id", membership.user_id).eq("group_id", membership.group_id).execute()
        elif operation == "delete":
            supabase.table("group_members").delete().eq("user_id", membership.user_id).eq("group_id", membership.group_id).execute()
            
    except Exception as e:
        print(f"Warning: Failed to sync membership to Supabase: {e}")


@router.post("/supabase_create", response_model=GroupOut)
async def create_group(
    group: GroupCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Create a new group with Supabase synchronization
    
    Args:
        group: Group creation data
        
    Returns:
        GroupOut: Created group data
        
    Raises:
        HTTPException: 400 if validation fails, 500 if creation fails
    """
    try:
        # Validate group data
        if not group.name or len(group.name.strip()) < 2:
            raise HTTPException(status_code=400, detail="Group name must be at least 2 characters long")
        
        if len(group.name) > 100:
            raise HTTPException(status_code=400, detail="Group name cannot exceed 100 characters")
        
        if group.description and len(group.description) > 500:
            raise HTTPException(status_code=400, detail="Group description cannot exceed 500 characters")
        
        # Generate unique invite code
        invite_code = generate_invite_code()
        while db.query(Group).filter(Group.invite_code == invite_code).first():
            invite_code = generate_invite_code()
        
        # Create group in local database
        new_group = Group(
            name=group.name.strip(),
            description=group.description.strip() if group.description else None,
            creator_id=current_user.id,
            invite_code=invite_code
        )
        db.add(new_group)
        db.commit()
        db.refresh(new_group)
        
        # Add creator as super-admin (role_id = 1)
        creator_membership = GroupMember(
            user_id=current_user.id, 
            group_id=new_group.id, 
            role_id=1
        )
        db.add(creator_membership)
        db.commit()
        
        # Sync to Supabase
        sync_group_to_supabase(new_group, "create")
        sync_membership_to_supabase(creator_membership, "create")
        
        # Return properly formatted response
        return {
            "id": new_group.id,
            "name": new_group.name,
            "description": new_group.description,
            "invite_code": new_group.invite_code,
            "created_at": new_group.created_at,
            "creator": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "bio": current_user.bio,
                "created_at": current_user.created_at,
                "profile_picture": current_user.profile_picture
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create group: {str(e)}")


@router.post("/supabase_join")
async def join_group(
    join: GroupJoin, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Join a group using an invite code
    
    Args:
        join: Group join data with invite code
        
    Returns:
        dict: Success message with group information
        
    Raises:
        HTTPException: 404 if group not found, 400 if already joined, 500 if join fails
    """
    try:
        # Find group by invite code
        group = db.query(Group).filter(Group.invite_code == join.invite_code.upper()).first()
        if not group:
            raise HTTPException(status_code=404, detail="Invalid invite code")
        
        # Check if user already joined
        existing_membership = db.query(GroupMember).filter_by(
            user_id=current_user.id, 
            group_id=group.id
        ).first()
        if existing_membership:
            raise HTTPException(status_code=400, detail="You are already a member of this group")
        
        # Add user as restricted viewer (role_id = 5)
        new_membership = GroupMember(
            user_id=current_user.id, 
            group_id=group.id, 
            role_id=5
        )
        db.add(new_membership)
        db.commit()
        
        # Sync to Supabase
        sync_membership_to_supabase(new_membership, "create")
        
        return {
            "message": f"Successfully joined group '{group.name}'",
            "group": {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "invite_code": group.invite_code
            },
            "role": "restricted-viewer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to join group: {str(e)}")


@router.get("/supabase_my", response_model=List[GroupOut])
async def get_my_groups(
    include_stats: bool = Query(False, description="Include group statistics"),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Get all groups the current user is a member of
    
    Args:
        include_stats: Whether to include group statistics
        
    Returns:
        List[GroupOut]: List of user's groups
        
    Raises:
        HTTPException: 404 if no groups found, 500 if query fails
    """
    try:
        # Get user's groups with creator info using join for efficiency
        groups_with_membership = db.query(Group, GroupMember, User).join(
            GroupMember, Group.id == GroupMember.group_id
        ).join(
            User, Group.creator_id == User.id
        ).filter(
            GroupMember.user_id == current_user.id
        ).all()
        
        if not groups_with_membership:
            return []
        
        # Process results
        result = []
        for group, membership, creator in groups_with_membership:
            group_data = {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "creator_id": group.creator_id,
                "invite_code": group.invite_code,
                "created_at": group.created_at,
                "creator": {
                    "id": creator.id,
                    "name": creator.name,
                    "email": creator.email,
                    "bio": creator.bio,
                    "created_at": creator.created_at,
                    "profile_picture": creator.profile_picture
                }
            }
            
            # Add user's role in this group
            group_data["user_role_id"] = membership.role_id
            
            if include_stats:
                # Add group statistics
                from models.photo import Photo
                photo_count = db.query(Photo).filter(Photo.group_id == group.id).count()
                member_count = db.query(GroupMember).filter(GroupMember.group_id == group.id).count()
                
                group_data["stats"] = {
                    "total_photos": photo_count,
                    "total_members": member_count
                }
            
            result.append(group_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get groups: {str(e)}")


@router.get("/supabase_group/{group_id}", response_model=GroupOut)
async def get_group_details(
    group_id: int = Path(..., gt=0), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific group
    
    Args:
        group_id: ID of the group to retrieve
        
    Returns:
        GroupOut: Detailed group information
        
    Raises:
        HTTPException: 404 if group not found, 403 if not member, 500 if query fails
    """
    try:
        # Find group
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check if user is a member
        membership = db.query(GroupMember).filter_by(
            user_id=current_user.id,
            group_id=group.id
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this group")
        
        # Get group statistics
        from models.photo import Photo
        total_photos = db.query(Photo).filter(Photo.group_id == group.id).count()
        total_members = db.query(GroupMember).filter(GroupMember.group_id == group.id).count()
        
        # Get creator information
        creator = db.query(User).filter(User.id == group.creator_id).first()
        
        result = {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "creator_id": group.creator_id,
            "invite_code": group.invite_code,
            "created_at": group.created_at,
            "creator": {
                "id": creator.id,
                "name": creator.name,
                "email": creator.email,
                "bio": creator.bio,
                "created_at": creator.created_at,
                "profile_picture": creator.profile_picture
            } if creator else None,
            "user_role_id": membership.role_id,
            "stats": {
                "total_photos": total_photos,
                "total_members": total_members
            }
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get group details: {str(e)}")


@router.get("/supabase_group/{group_id}/members")
async def get_group_members(
    group_id: int = Path(..., gt=0), 
    include_roles: bool = Query(True, description="Include member roles"),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Get list of group members
    
    Args:
        group_id: ID of the group
        include_roles: Whether to include role information
        
    Returns:
        dict: Group members information
        
    Raises:
        HTTPException: 404 if group not found, 403 if not member, 500 if query fails
    """
    try:
        # Find group
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check if user is a member
        user_membership = db.query(GroupMember).filter_by(
            user_id=current_user.id, 
            group_id=group.id
        ).first()
        if not user_membership:
            raise HTTPException(status_code=403, detail="You are not a member of this group")
        
        # Get all members with their user information
        members_query = db.query(User, GroupMember).join(
            GroupMember, User.id == GroupMember.user_id
        ).filter(GroupMember.group_id == group_id)
        
        members_data = []
        for user, membership in members_query.all():
            member_info = {
                "user_id": user.id,
                "name": user.name,
                "email": user.email if user_membership.role_id in [1, 2] else None,  # Only admins see emails
                "profile_picture": user.profile_picture
            }
            
            if include_roles:
                # Get role information
                role = db.query(GroupRole).filter(GroupRole.id == membership.role_id).first()
                member_info["role"] = {
                    "id": membership.role_id,
                    "name": role.name if role else "Unknown"
                }
            
            members_data.append(member_info)
        
        return {
            "group": {
                "id": group.id,
                "name": group.name
            },
            "members": members_data,
            "total_count": len(members_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get group members: {str(e)}")


@router.delete("/supabase_group/{group_id}/leave")
async def leave_group(
    group_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Leave a group
    
    Args:
        group_id: ID of the group to leave
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if group not found, 400 if not member or owner, 500 if operation fails
    """
    try:
        # Find group
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Find membership
        membership = db.query(GroupMember).filter_by(
            user_id=current_user.id, 
            group_id=group_id
        ).first()
        if not membership:
            raise HTTPException(status_code=400, detail="You are not a member of this group")
        
        # Check if user is the owner (role_id = 1)
        if membership.role_id == 1:
            raise HTTPException(status_code=403, detail="Group owner cannot leave the group. Transfer ownership or delete the group instead.")
        
        # Remove membership
        db.delete(membership)
        db.commit()
        
        # Sync to Supabase
        sync_membership_to_supabase(membership, "delete")
        
        return {
            "message": f"Successfully left group '{group.name}'",
            "group_id": group_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to leave group: {str(e)}")


@router.delete("/supabase_group/{group_id}")
async def delete_group(
    group_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Delete a group (owner only)
    
    Args:
        group_id: ID of the group to delete
        
    Returns:
        dict: Success message with deletion summary
        
    Raises:
        HTTPException: 404 if group not found, 403 if not owner, 500 if deletion fails
    """
    try:
        # Find group
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check if user is the owner
        membership = db.query(GroupMember).filter_by(
            user_id=current_user.id, 
            group_id=group_id
        ).first()
        if not membership or membership.role_id != 1:
            raise HTTPException(status_code=403, detail="Only the group owner can delete this group")
        
        group_name = group.name
        
        # Delete all group photos and their files
        from models.photo import Photo
        from utils.storage import delete_file
        
        group_photos = db.query(Photo).filter(Photo.group_id == group_id).all()
        deleted_photos = 0
        for photo in group_photos:
            try:
                await delete_file(photo.file_path)
                deleted_photos += 1
            except Exception as e:
                print(f"Warning: Could not delete photo file {photo.file_path}: {e}")
            db.delete(photo)
        
        # Delete all group memberships
        group_memberships = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
        for membership in group_memberships:
            sync_membership_to_supabase(membership, "delete")
            db.delete(membership)
        
        # Delete the group
        sync_group_to_supabase(group, "delete")
        db.delete(group)
        db.commit()
        
        return {
            "message": f"Group '{group_name}' deleted successfully",
            "deleted_data": {
                "group_id": group_id,
                "photos_deleted": deleted_photos,
                "members_removed": len(group_memberships)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete group: {str(e)}")


@router.put("/supabase_group/{group_id}/update", response_model=GroupOut)
async def update_group(
    group_id: int, 
    group_data: GroupUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Update group information (owner/admin only)
    
    Args:
        group_id: ID of the group to update
        group_data: Updated group data
        
    Returns:
        GroupOut: Updated group data
        
    Raises:
        HTTPException: 404 if group not found, 403 if not authorized, 500 if update fails
    """
    try:
        # Find group
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check if user has permission (owner or admin)
        membership = db.query(GroupMember).filter_by(
            user_id=current_user.id, 
            group_id=group_id
        ).first()
        if not membership or membership.role_id not in [1, 2]:
            raise HTTPException(status_code=403, detail="Only group owner or admin can update group information")
        
        # Update group data
        if group_data.name is not None:
            name = group_data.name.strip()
            if len(name) < 2:
                raise HTTPException(status_code=400, detail="Group name must be at least 2 characters long")
            if len(name) > 100:
                raise HTTPException(status_code=400, detail="Group name cannot exceed 100 characters")
            group.name = name
        
        if group_data.description is not None:
            description = group_data.description.strip() if group_data.description else None
            if description and len(description) > 500:
                raise HTTPException(status_code=400, detail="Group description cannot exceed 500 characters")
            group.description = description
        
        db.commit()
        db.refresh(group)
        
        # Sync to Supabase
        sync_group_to_supabase(group, "update")
        
        # Get creator information for response
        creator = db.query(User).filter(User.id == group.creator_id).first()
        
        # Return properly formatted response
        return {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "invite_code": group.invite_code,
            "created_at": group.created_at,
            "creator": {
                "id": creator.id,
                "name": creator.name,
                "email": creator.email,
                "bio": creator.bio,
                "created_at": creator.created_at,
                "profile_picture": creator.profile_picture
            } if creator else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update group: {str(e)}")


@router.put("/supabase_group/{group_id}/member/{member_id}/role")
async def update_member_role(
    group_id: int, 
    member_id: int, 
    new_role_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Update a member's role in the group
    
    Args:
        group_id: ID of the group
        member_id: ID of the member to update
        new_role_id: New role ID for the member
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if not found, 403 if not authorized, 400 if invalid role, 500 if update fails
    """
    try:
        # Find group
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check if current user has permission (owner or admin)
        current_user_membership = db.query(GroupMember).filter_by(
            user_id=current_user.id, 
            group_id=group_id
        ).first()
        if not current_user_membership or current_user_membership.role_id not in [1, 2]:
            raise HTTPException(status_code=403, detail="Only group owner or admin can update member roles")
        
        # Find member to update
        member_membership = db.query(GroupMember).filter_by(
            user_id=member_id, 
            group_id=group_id
        ).first()
        if not member_membership:
            raise HTTPException(status_code=404, detail="Member not found in this group")
        
        # Validate new role
        valid_roles = [1, 2, 3, 4, 5]  # super-admin, admin, contributor, viewer, restricted-viewer
        if new_role_id not in valid_roles:
            raise HTTPException(status_code=400, detail="Invalid role ID")
        
        # Prevent non-owners from assigning owner role
        if new_role_id == 1 and current_user_membership.role_id != 1:
            raise HTTPException(status_code=403, detail="Only the group owner can assign owner role")
        
        # Prevent changing owner role (must use transfer ownership)
        if member_membership.role_id == 1:
            raise HTTPException(status_code=400, detail="Cannot change owner role. Use transfer ownership instead.")
        
        # Update role
        old_role_id = member_membership.role_id
        member_membership.role_id = new_role_id
        db.commit()
        
        # Sync to Supabase
        sync_membership_to_supabase(member_membership, "update")
        
        # Get role names for response
        old_role = db.query(GroupRole).filter(GroupRole.id == old_role_id).first()
        new_role = db.query(GroupRole).filter(GroupRole.id == new_role_id).first()
        
        return {
            "message": "Member role updated successfully",
            "member_id": member_id,
            "group_id": group_id,
            "role_change": {
                "from": old_role.name if old_role else "Unknown",
                "to": new_role.name if new_role else "Unknown"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update member role: {str(e)}")


@router.put("/supabase_group/{group_id}/transfer_ownership")
async def transfer_group_ownership(
    group_id: int, 
    new_owner_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Transfer group ownership to another member
    
    Args:
        group_id: ID of the group
        new_owner_id: ID of the user to transfer ownership to
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if not found, 403 if not authorized, 400 if invalid transfer, 500 if transfer fails
    """
    try:
        # Prevent self-transfer
        if new_owner_id == current_user.id:
            raise HTTPException(status_code=400, detail="You are already the owner of this group")
        
        # Find group
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check if current user is the owner
        current_owner = db.query(GroupMember).filter_by(
            group_id=group_id, 
            user_id=current_user.id
        ).first()
        if not current_owner or current_owner.role_id != 1:
            raise HTTPException(status_code=403, detail="Only the current group owner can transfer ownership")
        
        # Find new owner
        new_owner_user = db.query(User).filter(User.id == new_owner_id).first()
        if not new_owner_user:
            raise HTTPException(status_code=404, detail="New owner user not found")
        
        # Check if new owner is a group member
        new_owner_membership = db.query(GroupMember).filter_by(
            user_id=new_owner_id, 
            group_id=group_id
        ).first()
        if not new_owner_membership:
            raise HTTPException(status_code=404, detail="New owner is not a member of this group")
        
        # Transfer ownership
        new_owner_membership.role_id = 1  # Set as super-admin
        current_owner.role_id = 2  # Demote to admin
        
        db.commit()
        
        # Sync to Supabase
        sync_membership_to_supabase(new_owner_membership, "update")
        sync_membership_to_supabase(current_owner, "update")
        
        return {
            "message": f"Ownership of group '{group.name}' transferred to {new_owner_user.name} successfully",
            "group_id": group_id,
            "new_owner": {
                "id": new_owner_user.id,
                "name": new_owner_user.name,
                "email": new_owner_user.email
            },
            "previous_owner": {
                "id": current_user.id,
                "name": current_user.name,
                "new_role": "admin"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to transfer ownership: {str(e)}")


@router.get("/supabase_group/{group_id}/analytics")
async def get_group_analytics(
    group_id: int = Path(..., gt=0),
    days: int = Query(30, ge=1, le=365, description="Number of days for analytics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get group analytics and statistics
    
    Args:
        group_id: ID of the group
        days: Number of days to include in analytics
        
    Returns:
        dict: Group analytics data
        
    Raises:
        HTTPException: 404 if group not found, 403 if not authorized, 500 if query fails
    """
    try:
        # Find group and check membership
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        membership = db.query(GroupMember).filter_by(
            user_id=current_user.id,
            group_id=group_id
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this group")
        
        # Only admin and owner can see detailed analytics
        if membership.role_id not in [1, 2]:
            raise HTTPException(status_code=403, detail="Only group admin or owner can view analytics")
        
        from models.photo import Photo
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Basic statistics
        total_members = db.query(GroupMember).filter(GroupMember.group_id == group_id).count()
        total_photos = db.query(Photo).filter(Photo.group_id == group_id).count()
        
        # Recent photos (within the specified days)
        recent_photos = db.query(Photo).filter(
            Photo.group_id == group_id,
            Photo.created_at >= start_date
        ).count()
        
        # Storage usage
        group_photos = db.query(Photo).filter(Photo.group_id == group_id).all()
        total_storage = 0
        for photo in group_photos:
            try:
                import os
                if photo.file_path and os.path.exists(photo.file_path):
                    total_storage += os.path.getsize(photo.file_path)
            except Exception:
                pass
        
        # Member roles distribution
        role_distribution = {}
        memberships = db.query(GroupMember, GroupRole).join(
            GroupRole, GroupMember.role_id == GroupRole.id
        ).filter(GroupMember.group_id == group_id).all()
        
        for membership, role in memberships:
            role_name = role.name
            role_distribution[role_name] = role_distribution.get(role_name, 0) + 1
        
        # Top contributors (most photos uploaded)
        top_contributors = db.query(
            User.name, 
            func.count(Photo.id).label('photo_count')
        ).join(Photo, User.id == Photo.uploader_id)\
         .filter(Photo.group_id == group_id)\
         .group_by(User.id, User.name)\
         .order_by(func.count(Photo.id).desc())\
         .limit(5).all()
        
        analytics = {
            "group_id": group_id,
            "group_name": group.name,
            "period_days": days,
            "basic_stats": {
                "total_members": total_members,
                "total_photos": total_photos,
                "recent_photos": recent_photos,
                "total_storage_bytes": total_storage,
                "storage_mb": round(total_storage / (1024 * 1024), 2)
            },
            "member_roles": role_distribution,
            "top_contributors": [
                {"name": name, "photo_count": count} 
                for name, count in top_contributors
            ],
            "activity_summary": {
                "photos_per_day": round(recent_photos / days, 2) if days > 0 else 0,
                "average_photos_per_member": round(total_photos / total_members, 2) if total_members > 0 else 0
            }
        }
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get group analytics: {str(e)}") 