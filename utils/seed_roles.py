from models.groupRoles import GroupRole

def seed_roles(db):
    existing_roles = db.query(GroupRole).count()
    if existing_roles > 0:
        return  
    
    roles = ["super-admin", "admin", "collaborator", "full-viewer", "restricted-viewer"]
    for i, name in enumerate(roles, start=1):
        if not db.query(GroupRole).filter_by(name=name).first():
            db.add(GroupRole(id=i, name=name))  
    db.commit()

