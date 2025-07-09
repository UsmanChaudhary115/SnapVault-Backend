from fastapi import FastAPI
from database import engine, Base
from routes import auth, group, photo  # 👈 Import both routers
import models

app = FastAPI()

Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(group.router, prefix="/groups", tags=["Groups"])  # 👈 Add this line
app.include_router(photo.router, prefix="/photos", tags=["Photos"])  # 👈 Add this line

@app.get("/")
async def root():
    return {"message": "Welcome to SnapVault!"}

