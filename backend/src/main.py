from fastapi import FastAPI
from dotenv import load_dotenv
from src.api.routers import workspace, auth, marketplace

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="KgpOne Backend API")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(marketplace.router, prefix="/marketplace", tags=["marketplace"])
app.include_router(workspace.router, prefix="/workspace", tags=["workspace"])

@app.get("/")
def read_root():
    return {"message": "Welcome to KgpOne API"}
