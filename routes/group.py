import random, string
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from database import get_db
from models.group import Group
from models.group_member import GroupMember
from schemas.group import GroupCreate, GroupJoin, GroupOut
from utils.auth_utils import get_current_user
from models.user import User

router = APIRouter(prefix="/groups", tags=["Groups"])
 
def generate_invite_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ✅ Create Group
@router.post("/create", response_model=GroupOut)
def create_group(group: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invite_code = generate_invite_code()
    while db.query(Group).filter(Group.invite_code == invite_code).first():
        invite_code = generate_invite_code()

    new_group = Group(
        name=group.name,
        creator_id=current_user.id,
        invite_code=invite_code
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    # Also add creator as member
    member = GroupMember(user_id=current_user.id, group_id=new_group.id)
    db.add(member)
    db.commit()

    return new_group


# ✅ Join Group
@router.post("/join")
def join_group(join: GroupJoin, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.invite_code == join.invite_code).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Prevent double joining
    already_joined = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=group.id).first()
    if already_joined:
        raise HTTPException(status_code=400, detail="You already joined this group")
    new_member = GroupMember(user_id=current_user.id, group_id=group.id)
    db.add(new_member)
    db.commit()
    return {"message": f"Joined group '{group.name}' successfully."}

    # ✅ List groups the current user has joined
@router.get("/my", response_model=list[GroupOut])
def get_my_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member_entries = db.query(GroupMember).filter_by(user_id=current_user.id).all()
    group_ids = [entry.group_id for entry in member_entries]
    groups = db.query(Group).filter(Group.id.in_(group_ids)).all()
    return groups


# ✅ Get group details by ID
# @router.get("/{id}", response_model=GroupOut)
# def get_group(id: int = Path(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     group = db.query(Group).filter(Group.id == id).first()
#     if not group:
#         raise HTTPException(status_code=404, detail="Group not found")
#     return group

@router.get("/{id}", response_model=GroupOut)
def get_group(
    id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    group = db.query(Group).filter(Group.id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # ✅ Check if current_user is a member of the group
    membership = db.query(GroupMember).filter_by(
        user_id=current_user.id,
        group_id=group.id
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this group")

    return group



# ✅ List all members of a group
@router.get("/{id}/members")
def get_group_members(id: int = Path(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.id == id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found") 
    members_raw = (
    db.query(User.id, User.name, User.email, User.bio)
    .join(GroupMember, User.id == GroupMember.user_id)
    .filter(GroupMember.group_id == id)
    .all()
    )

    members = [
        {"name": m[1],  "bio": m[3]} for m in members_raw
    ]
    return {"group": group.name, "members": members}