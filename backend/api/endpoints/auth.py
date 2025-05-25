import os
import time
import uuid
import secrets
import hashlib
import base64

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Response

from fastapi.responses import RedirectResponse
from starlette.requests import Request
from keycloak import KeycloakOpenID


load_dotenv()
router = APIRouter()

# Keycloakクライアントの初期化
keycloak_openid = KeycloakOpenID(
    server_url=os.getenv("KEYCLOAK_URL"),
    client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
    realm_name=os.getenv("KEYCLOAK_REALM"),
    client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET"),
    verify=True
)


def generate_pkce_pair():
    """PKCEのためのcode_verifierとcode_challengeを生成する."""
    verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


@router.get("/login")
def login(request: Request, state: str = "/"):
    """Keycloakの認証エンドポイントにリダイレクトする."""
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
            scope="openid email roles",
            state=state,
            nonce=request.session["nonce"]
        )
        # ログインURLにリダイレクト
        return RedirectResponse(redirect_url)

    except Exception as e:
        raise HTTPException(
                status_code=500,
                detail=f"Login failed {e}"
        )


@router.get("/callback")
def callback(
        response: Response,
        request: Request,
        code: str,
        state: str
     ) -> dict:
    """Keycloakの認証コールバックエンドポイント. Keycloakからの認証コードを受け取り, アクセストークンを取得する."""
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

        # クッキーにアクセストークンを格納する
        for name, value, age in [
            (
                "access_token",
                tokens["access_token"],
                tokens["expires_in"]
            ),
            (
                "refresh_token",
                tokens["refresh_token"],
                tokens.get("refresh_expires_in", 86400)
            ),
        ]:
            response.set_cookie(
                key=name,
                value=value,
                httponly=True,       # JavaScriptからアクセスできない
                secure=False,        # HTTPS 本番ではTrue
                samesite="lax",      # CSRF対策
                max_age=age,         # 有効期限
            )

        # SPAへのリダイレクトはコメントアウト
        # return RedirectResponse(
        #     f"{os.getenv('FRONTEND_URL')}{state}"
        # )
        return {"access_token": request.session["access_token"]}
    except Exception as e:
        raise HTTPException(
                status_code=500,
                detail=f"Callback failed {e}"
        )
