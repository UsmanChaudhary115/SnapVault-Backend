from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal 
from routes import auth, group, photo, user 
from utils.seed_db import seed_roles, seed_group_claims, seed_group_role_claims
import os


def create_required_folders():
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("uploads/profile_pictures", exist_ok=True)
    os.makedirs("uploads/photos", exist_ok=True)


app = FastAPI()
create_required_folders()
#Base.metadata.create_all(bind=engine)
 
with SessionLocal() as db:
    seed_roles(db)
    seed_group_claims(db)
    seed_group_role_claims(db)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads folder
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads") 

# Local routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(group.router, prefix="/groups", tags=["Groups"])
app.include_router(photo.router, prefix="/photos", tags=["Photos"])  


@app.get("/")
async def root():
    return {"message": "Welcome to SnapVault!"}