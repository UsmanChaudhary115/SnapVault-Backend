import random, string
from fastapi import APIRouter, Depends, HTTPException, Path # type: ignore
from sqlalchemy.orm import Session # type: ignore
from database import get_db
from models.group import Group
from models.groupRoles import GroupRole
from models.group_member import GroupMember
from schemas.group import GroupCreate, GroupJoin, GroupOut, GroupUpdate
from utils.auth_utils import get_current_user
from models.user import User

router = APIRouter()
 
def generate_invite_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

 
@router.post("/create", response_model=GroupOut)
def create_group(group: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    invite_code_raw = generate_invite_code()
    while db.query(Group).filter(Group.invite_code == invite_code_raw).first():
        invite_code_raw = generate_invite_code()

    new_group = Group(
        name=group.name,
        description=group.description,
        creator_id=current_user.id, 
        invite_code=invite_code_raw
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

 
    member = GroupMember(user_id=current_user.id, group_id=new_group.id, role_id = 1) # assuming 1 is the ID for "super-admin"
    db.add(member)
    db.commit()

    return new_group


 
@router.post("/join")
def join_group(join: GroupJoin, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.invite_code == join.invite_code).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

 
    already_joined = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=group.id).first()
    if already_joined:
        raise HTTPException(status_code=400, detail="You already joined this group")
    
    
    new_member = GroupMember(user_id=current_user.id, group_id=group.id, role_id = 5) # assuming 5 is the ID for "restricted-viewer"
    db.add(new_member)
    db.commit()
    return {"message": f"Joined group '{group.name}' successfully."}

 

@router.get("/my", response_model=list[GroupOut])
def get_my_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member_entries = db.query(GroupMember).filter_by(user_id=current_user.id).all()
    if not member_entries:
        raise HTTPException(status_code=404, detail="You are not a member of any groups")
    group_ids = [entry.group_id for entry in member_entries]
    groups = db.query(Group).filter(Group.id.in_(group_ids)).all()
    return groups
 
@router.get("/{id}", response_model=GroupOut)
def get_group(id: int = Path(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
 
    membership = db.query(GroupMember).filter_by(
        user_id=current_user.id,
        group_id=group.id
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this group")

    return group



 
@router.get("/{id}/members")
def get_group_members(id: int = Path(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found") 
    
    membership = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=group.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    
    member_names = (
    db.query(User.name).join(GroupMember, User.id == GroupMember.user_id).filter(GroupMember.group_id == id).all())

    members = [name for (name,) in member_names]

    return {"group": group.name, "members": members}



@router.delete("/{id}/leave")
def leave_group(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    membership = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=id).first()
    if not membership:
        raise HTTPException(status_code=400, detail="You're not a member of this group")
 
    if membership.role_id == 1:
        raise HTTPException(status_code=403, detail="Owner cannot leave their own group")

    db.delete(membership)
    db.commit()

    return {"message": f"Left group '{group.name}' successfully"}


@router.delete("/{id}")
def delete_group(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    (role_id,) = db.query(GroupMember.role_id).filter_by(user_id=current_user.id, group_id=id).first() or (None,)
    if role_id != 1:
        raise HTTPException(status_code=403, detail="Only the group owner can delete this group")

 
    db.query(GroupMember).filter(GroupMember.group_id == id).delete()  # Remove all members from the group 

    db.delete(group)
    db.commit()

    return {"message": f"Group '{group.name}' deleted successfully"}
 
@router.put("/{id}/UpdateGroup", response_model=GroupOut)
def update_group(id: int, group_data: GroupUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    (role_id,) = db.query(GroupMember.role_id).filter_by(user_id=current_user.id, group_id=id).first() or (None,)
    if role_id != 1:
        raise HTTPException(status_code=403, detail="Only the group owner can update this group information")

    if group_data.name is not None: 
        group.name = group_data.name
    if group_data.description is not None:
        group.description = group_data.description
    
    db.commit()
    db.refresh(group)

    return group

@router.put("/{id}/update_group_access")
def update_group_access_for_member(id: int, member_id: int, role_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    group = db.query(Group).filter(Group.id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    (role_id_current,) = db.query(GroupMember.role_id).filter_by(user_id=current_user.id, group_id=id).first() or (None,)
    if role_id_current != 1 and role_id_current != 2: 
        raise HTTPException(status_code=403, detail="Only admin can update member access")

    member = db.query(GroupMember).filter_by(user_id=member_id, group_id=id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this group")

    member.role_id = role_id
    db.commit()
    db.refresh(member)
 
    return {"The group access has been updated for the member"}

@router.put("/{id}/transfer_ownership")
def transfer_group_ownership(id: int, new_owner_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    if new_owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="You are already the super-admin")
    
    group = db.query(Group).filter(Group.id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    caller = db.query(GroupMember).filter_by(group_id=id, user_id=current_user.id).first()
    if not caller or caller.role_id != 1:
        raise HTTPException(status_code=403, detail="Only the current super-admin can transfer ownership")
    


    user = db.query(User).filter(User.id == new_owner_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="New owner not found")
    
    owner_to_be = db.query(GroupMember).filter_by(user_id=new_owner_id, group_id=id).first()
    if not owner_to_be:
        raise HTTPException(status_code=404, detail="New owner is not a member of this group")

    owner_to_be.role_id = 1 # Change new owner to super-admin 
    caller.role_id = 2  # Change current owner to admin 
    db.commit()
    db.refresh(caller)
    db.refresh(owner_to_be)
    return {"message": f"Ownership of group '{group.name}' transferred to {user.name} successfully."}