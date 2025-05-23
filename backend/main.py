import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from api.api import api_router

# FastAPIのセットアップ
app = FastAPI(
    title="Backend APIs",
    openapi_url="/api/openapi.json"
)
app.include_router(api_router, prefix="/api")

# セッションミドルウェア
app.add_middleware(
    SessionMiddleware,
    secret_key=os.urandom(24),
    max_age=3600,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
