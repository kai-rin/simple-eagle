import os
import secrets
from fastapi import Request, HTTPException


EAGLE_AUTH_PASSWORD = os.getenv('EAGLE_AUTH_PASSWORD', '')
AUTH_ENABLED = bool(EAGLE_AUTH_PASSWORD)

# サーバー起動ごとにランダムなトークンを生成（再起動でセッション無効化）
AUTH_TOKEN = secrets.token_hex(32)


async def verify_auth(request: Request):
    """APIルーターの依存関数。認証が有効な場合、Cookieのトークンを検証する"""
    if not AUTH_ENABLED:
        return
    token = request.cookies.get('eagle_auth')
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


def verify_password(password: str) -> bool:
    """パスワードを検証する"""
    return secrets.compare_digest(password, EAGLE_AUTH_PASSWORD)
