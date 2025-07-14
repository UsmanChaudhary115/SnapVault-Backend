from fastapi import FastAPI
from database import engine, Base
import models  
from routes import auth, group, photo, testing, user
import os

def create_required_folders():
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("uploads/profile_pictures", exist_ok=True)
    os.makedirs("uploads/photos", exist_ok=True)


app = FastAPI()
create_required_folders()
Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(group.router, prefix="/groups", tags=["Groups"])  
app.include_router(photo.router, prefix="/photos", tags=["Photos"])   
app.include_router(testing.router, prefix="/testing", tags=["Testing"])

@app.get("/")
async def root():
    return {"message": "Welcome to SnapVault!"}

