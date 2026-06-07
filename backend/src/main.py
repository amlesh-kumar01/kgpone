from fastapi import FastAPI
from src.api.routers import workspace, auth, marketplace

app = FastAPI(title="KgpOne Backend API")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(marketplace.router, prefix="/marketplace", tags=["marketplace"])
app.include_router(workspace.router, prefix="/workspace", tags=["workspace"])

@app.get("/")
def read_root():
    return {"message": "Welcome to KgpOne API"}
