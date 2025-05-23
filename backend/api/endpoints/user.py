import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from keycloak import KeycloakOpenID, KeycloakAdmin
from jose import jwt, JWTError
import httpx

load_dotenv()
router = APIRouter()

keycloak_client_id = os.getenv("KEYCLOAK_CLIENT_ID")
keycloak_realm = os.getenv("KEYCLOAK_REALM")

# Keycloakクライアントの初期化
keycloak_openid = KeycloakOpenID(
    server_url="http://localhost:8080/",
    client_id=keycloak_client_id,
    realm_name=keycloak_realm,
    client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET"),
    verify=True
)

keycloak_admin = KeycloakAdmin(
    server_url="http://localhost:8080/",
    client_id=keycloak_client_id,
    realm_name=keycloak_realm,
    client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET"),
)

bearer_scheme = HTTPBearer()


async def verify_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict[str, any]:
    """
    HTTP AuthorizationヘッダーのBearerトークンを検証し、
    トークン内のペイロードを返す.
    """
    token = credentials.credentials

    try:
        # トークンからヘッダー部分を取り出し、kid（Key ID）を取得
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: No key ID")

        # JWKS取得
        jwks_url = "http://localhost:8080/realms/" + \
            f"{keycloak_realm}/protocol/openid-connect/certs"
        async with httpx.AsyncClient() as client:
            jwks_response = await client.get(jwks_url)
            jwks = jwks_response.json()

        # 適切な公開鍵を見つける
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = {
                    "kty": key.get("kty"),
                    "kid": key.get("kid"),
                    "use": key.get("use"),
                    "n": key.get("n"),
                    "e": key.get("e")
                }

        if not rsa_key:
            raise HTTPException(status_code=401, detail="Public key not found")

        # 発行者（Issuer）の設定
        issuer = f"http://localhost:8080/realms/{keycloak_realm}"

        # トークン検証（署名、audience、発行者、有効期限）
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=keycloak_client_id,  # audience検証を有効に
            issuer=issuer,
            options={
                "verify_signature": True,
                "verify_aud": False,
                "verify_exp": True
            }
        )

        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired token: {e}"
        )


async def require_admin_role(
    payload: dict[str, any] = Depends(verify_access_token)
) -> dict[str, any]:
    """
    トークンペイロード内の Client Roles を調べ、
    'admin' が含まれていなければ403を返すDepends関数.
    """
    # resource_access → { CLIENT_ID: { roles: [...] } }
    resource_access = payload.get("resource_access", {})
    client_access = resource_access.get(keycloak_client_id, {})
    roles = client_access.get("roles", [])

    if "fastapi_admin" not in roles:
        raise HTTPException(
            status_code=403,
            detail="Admin role required"
        )
    return payload


async def require_user_role(
    payload: dict[str, any] = Depends(verify_access_token)
) -> dict[str, any]:
    """
    トークンペイロード内の Client Roles を調べ、
    'fastapi_user' が含まれていなければ403を返すDepends関数.
    """
    # resource_access → { CLIENT_ID: { roles: [...] } }
    resource_access = payload.get("resource_access", {})
    client_access = resource_access.get(keycloak_client_id, {})
    roles = client_access.get("roles", [])

    if "fastapi_user" not in roles and "fastapi_admin" not in roles:
        raise HTTPException(
            status_code=403,
            detail="User role required"
        )
    return payload


def create_user_with_password(
        email: str,
        password: str,
        roles: list[str],
        first_name: str | None = None,
        last_name: str | None = None):
    """ユーザーを新規作成する."""
    # 今回はパスワード付きのユーザーを作成する
    # パスワードリセット付きメールを送り
    # ユーザーにパスワードリセットリンクが記載されたメールが届くパターンもある
    user = {
        "email": email,
        "enabled": True,
        "credentials": [{"type": "password", "value": password}]
    }
    if first_name is not None:
        user["firstName"] = first_name
    if last_name is not None:
        user["lastName"] = last_name

    user_id = keycloak_admin.create_user(user, exist_ok=False)

    if len(roles) > 0:
        try:
            defined_client_roles = keycloak_admin.get_client_roles(
                client_id=keycloak_client_id
            )

            new_roles = []
            for role in roles:
                is_defined = False
                for dr in defined_client_roles:
                    if dr["name"] == role:
                        is_defined = True
                        new_roles.append(dr)
                        break
                if not is_defined:
                    raise ValueError(f"Role {role} is not defined")

            # ロール割り当て
            keycloak_admin.assign_realm_roles(
                user_id=user_id,
                roles=new_roles
            )
        except Exception as e:
            keycloak_admin.delete_user(user_id)
            raise e

    return user_id


@router.get("/profile")
def profile(payload: dict[str, any] = Depends(require_user_role)):
    """自分のプロフィール情報を取得する."""
    try:
        # トークンからユーザーIDを取得
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=404,
                                detail="User ID not found in token")

        # ユーザー情報を取得
        user_info = keycloak_admin.get_user(user_id)
        
        # 必要な情報だけを抽出して返す
        result = {
            "id": user_info.get("id"),
            "username": user_info.get("username"),
            "email": user_info.get("email"),
            "firstName": user_info.get("firstName"),
            "lastName": user_info.get("lastName"),
            "enabled": user_info.get("enabled"),
            "emailVerified": user_info.get("emailVerified"),
        }

        return result  # FastAPIがJSONに変換
    except Exception as e:
        raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve profile information: {e}"
        )


@router.get("/users")
def users(_: dict[str, any] = Depends(require_admin_role)):
    """ユーザー一覧を取得する."""
    try:
        all_users = keycloak_admin.get_users()

        # ユーザー情報を整形して返す
        formatted_users = []
        for user in all_users:
            formatted_users.append({
                "id": user.get("id"),
                "username": user.get("username"),
                "email": user.get("email"),
                "firstName": user.get("firstName"),
                "lastName": user.get("lastName"),
                "enabled": user.get("enabled")
            })

        return formatted_users  # FastAPIがJSONに変換
    except Exception as e:
        raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve users: {e}"
        )


@router.post("/user")
def user(email: str,
         password: str,
         role: str,
         first_name: str | None = None,
         last_name: str | None = None,
         _: dict[str, any] = Depends(require_admin_role)):
    """ユーザーを新規作成する."""
    try:
        create_user_with_password(
            email=email,
            password=password,
            roles=[role],
            first_name=first_name,
            last_name=last_name
        )
    except Exception as e:
        raise HTTPException(
                status_code=500,
                detail=f"Login failed {e}"
        )
