from fastapi import FastAPI
from database import engine, Base, SessionLocal 
from routes import auth, group, photo, testing, user, supabase_auth, supabase_user, supabase_group, supabase_photo
from utils.seed_roles import seed_roles
import os


def create_required_folders():
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("uploads/profile_pictures", exist_ok=True)
    os.makedirs("uploads/photos", exist_ok=True)


app = FastAPI()
create_required_folders()
Base.metadata.create_all(bind=engine)
 
with SessionLocal() as db:
    seed_roles(db)

 
# Local routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(group.router, prefix="/groups", tags=["Groups"])
app.include_router(photo.router, prefix="/photos", tags=["Photos"])
app.include_router(testing.router, prefix="/testing", tags=["Testing"])

# Supabase routes
app.include_router(supabase_auth.router, prefix="/auth", tags=["Supabase Auth"])
app.include_router(supabase_user.router, prefix="/user", tags=["Supabase User"])
app.include_router(supabase_group.router, prefix="/groups", tags=["Supabase Groups"])
app.include_router(supabase_photo.router, prefix="/photos", tags=["Supabase Photos"])
import sys
print("🐍 Running Python version:", sys.version)


@app.get("/")
async def root():
    return {"message": "Welcome to SnapVault!"}
