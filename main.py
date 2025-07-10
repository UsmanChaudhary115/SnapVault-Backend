from fastapi import FastAPI
from database import engine, Base
import models  
from routes import auth, group, photo, testing

app = FastAPI()

Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(group.router, prefix="/groups", tags=["Groups"])  
app.include_router(photo.router, prefix="/photos", tags=["Photos"])   
app.include_router(testing.router, prefix="/testing", tags=["Testing"])

@app.get("/")
async def root():
    return {"message": "Welcome to SnapVault!"}

