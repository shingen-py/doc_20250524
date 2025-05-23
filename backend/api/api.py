from fastapi import APIRouter
from api.endpoints import auth

# APIのルーターを作成
api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
