from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_marketplace_items():
    return []
