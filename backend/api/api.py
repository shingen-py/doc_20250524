from fastapi import APIRouter

from api.endpoints import auth
from api.endpoints import user

# APIのルーターを作成
api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
