from models.groupRoles import GroupRole
from models.groupRoleClaim import GroupRoleClaim
from models.groupClaims import GroupClaim

def seed_roles(db):
    existing_roles = db.query(GroupRole).count()
    
    if existing_roles > 0:
        return  
    
    roles = ["super-admin", "admin", "collaborator", "full-viewer", "restricted-viewer"]
    
    for i, name in enumerate(roles, start=1):
        if not db.query(GroupRole).filter_by(name=name).first():
            db.add(GroupRole(id=i, name=name))  
    db.commit()

def seed_group_claims(db):
    existing_claims = db.query(GroupClaim).count()
    if existing_claims > 0:
        return  
    
    # Removed create_group and join_group from the list
    claims = [
        "get_group", "edit_group", "leave_group", "delete_group", "transfer_ownership", 
        "activate/deactivate_group", "add_member", "remove_member", 
        "view_all_members", "update_member_role", 
        "view_your_photos", "view_all_photos", 
        "upload_photos", "delete_photos_from_group"
    ]
    
    for i, name in enumerate(claims, start=1):
        if not db.query(GroupClaim).filter_by(name=name).first():
            db.add(GroupClaim(id=i, name=name))  
    db.commit()

def seed_group_role_claims(db):
    existing_role_claims = db.query(GroupRoleClaim).count()
    if existing_role_claims > 0:
        return
     
    role_claims = [
        # Super-admin
        (1, 1),  # get_group
        (1, 2),  # edit groups 
        (1, 4),  # delete groups
        (1, 5),  # transfer ownership
        (1, 6),  # activate/deactivate groups
        (1, 7),  # add members
        (1, 8),  # remove members
        (1, 9),  # view all members
        (1, 10), # update member roles
        (1, 11), # view your own photos
        (1, 12), # view all photos
        (1, 13), # upload photos
        (1, 14), # delete photos from group

        # Admin
        (2, 1),  # get_group
        (2, 2),  # edit groups
        (2, 3),  # leave groups
        (2, 7),  # add members
        (2, 8),  # remove members
        (2, 9),  # view all members
        (2, 10), # update member roles
        (2, 11), # view your own photos
        (2, 12), # view all photos
        (2, 13), # upload photos
        (2, 14), # delete photos from group

        # Collaborator
        (3, 1),  # get_group
        (3, 3),  # leave groups
        (3, 11), # view your own photos
        (3, 12), # view all photos
        (3, 13), # upload photos

        # Full-viewer
        (4, 1),  # get_group
        (4, 3),  # leave groups
        (4, 11), # view your own photos
        (4, 12), # view all photos

        # Restricted-viewer
        (5, 1),  # get_group
        (5, 3),  # leave groups
        (5, 11)  # view your own photos
    ]
    
    for i, (role_id, claim_id) in enumerate(role_claims, start=1):
        if not db.query(GroupRoleClaim).filter_by(role_id=role_id, claim_id=claim_id).first():
            db.add(GroupRoleClaim(id=i, role_id=role_id, claim_id=claim_id))

    db.commit()
 