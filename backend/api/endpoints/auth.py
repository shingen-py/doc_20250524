import os
import time
import uuid
import secrets
import hashlib
import base64

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from keycloak import KeycloakOpenID


load_dotenv()
router = APIRouter()


# Keycloakクライアントの初期化
keycloak_openid = KeycloakOpenID(
    server_url="http://localhost:8080/",
    client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
    realm_name=os.getenv("KEYCLOAK_REALM")
)


def generate_pkce_pair():
    verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


@router.get("/login")
def login(request: Request, state: str = "/"):
    try:
        # PKCEのためのcode_verifierとcode_challengeを生成
        # verifier, challenge = generate_pkce_pair()

        # セッションにstateとnonce, verifierを保存
        request.session["state"] = state
        request.session["nonce"] = str(uuid.uuid4())  # CSRF対策
        # request.session["verifier"] = verifier

        # Keycloakの認証エンドポイントの取得
        redirect_url = keycloak_openid.auth_url(
            redirect_uri=os.getenv("CALLBACK_URL"),
            scope="openid email profile",
            state=state
        )
        # ログインURLにリダイレクト
        return RedirectResponse(redirect_url)

    except Exception as e:
        raise HTTPException(
                status_code=500,
                detail=f"Login failed {e}"
        )


@router.get("/callback")
def callback(request: Request, code: str, state: str):
    try:
        # stateの検証
        if request.session["state"] != state:
            raise HTTPException(
                status_code=400,
                detail="Invalid state"
            )

        # 認可コードを使ってトークンを取得
        tokens = keycloak_openid.token(
                    code=code,
                    grant_type="authorization_code",
                    redirect_uri=os.getenv("CALLBACK_URL")
                )

        # nonceの検証
        decoded_token = keycloak_openid.decode_token(
            token=tokens["id_token"]
        )
        if request.session["nonce"] != decoded_token["nonce"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid nonce"
            )

        # トークン情報をセッションに保存
        request.session["access_token"] = tokens["access_token"]
        request.session["refresh_token"] = tokens["refresh_token"]

        request.session["token_expires_in"] = time.time() + \
            tokens["expires_in"]
        request.session["reflesh_expires_in"] = time.time() + \
            tokens["refresh_expires_in"]

        # TOOD: クッキーにアクセストークンを保存する

        return RedirectResponse(
            f"{os.getenv('FRONTEND_URL')}/{state}"
        )
    except Exception as e:
        raise HTTPException(
                status_code=500,
                detail=f"Callback failed {e}"
        )
