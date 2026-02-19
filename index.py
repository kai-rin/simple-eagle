from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
import base64
import os
import requests
import io
import socket
import qrcode
from modules.eagle_api import eagle_api
from modules.auth import verify_auth, verify_password, AUTH_ENABLED, AUTH_TOKEN

class ImageRequest(BaseModel):
    path: str

class UpdateRequest(BaseModel):
    id: str
    tags: list[str] | None = None
    annotation: str | None = None
    url: str | None = None
    star: int | None = None

class MoveToTrashRequest(BaseModel):
    itemIds: list[str]

app = FastAPI()
# GZip圧縮を有効化
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 認証ルーター（認証不要）
from fastapi import APIRouter, Request

class LoginRequest(BaseModel):
    password: str

auth_router = APIRouter()

@auth_router.get("/check")
async def auth_check(request: Request):
    """認証状態を確認"""
    if not AUTH_ENABLED:
        return {"status": "ok", "auth_enabled": False}
    token = request.cookies.get('eagle_auth')
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"status": "ok", "auth_enabled": True}

@auth_router.post("/login")
async def auth_login(request: LoginRequest):
    """パスワードを検証してセッションCookieを発行"""
    if not AUTH_ENABLED:
        return {"status": "ok"}
    if not verify_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    response = JSONResponse(content={"status": "ok"})
    response.set_cookie(
        key="eagle_auth",
        value=AUTH_TOKEN,
        httponly=True,
        samesite="strict",
    )
    return response

@auth_router.get("/server-info")
async def server_info(request: Request):
    """LAN内アクセス用のURL情報を返す"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"
    port = request.url.port or 80
    url = f"http://{ip}:{port}"
    return {"ip": ip, "port": port, "url": url}

@auth_router.get("/qrcode")
async def get_qrcode(url: str):
    """指定URLのQRコード画像を生成して返す"""
    qr = qrcode.QRCode(version=1, box_size=8, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")

# APIルーター（認証必須）
api_router = APIRouter(dependencies=[Depends(verify_auth)])

@api_router.get("/list")
async def get_list(
    limit: int = 200,
    offset: int = 0,
    orderBy: str = None,
    keyword: str = None,
    ext: str = None,
    tags: str = None,
    folders: str = None
):
    """
    Eagle APIから最新の画像一覧を取得
    Args:
        limit (int): 取得する画像の最大数（デフォルト: 100）
        folder_id (str, optional): 指定されたフォルダーIDの画像のみを取得
    """
    try:
        if folders == "uncategorized":
            return eagle_api.get_uncategorized_list(limit=limit, offset=offset)
        return eagle_api.get_list(
            limit=limit,
            offset=offset,
            orderBy=orderBy,
            keyword=keyword,
            ext=ext,
            tags=tags,
            folders=folders
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/folders")
async def get_folders():
    """
    Eagle APIからフォルダ一覧を取得
    """
    try:
        return eagle_api.get_folder_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/get_thumbnail_image")
async def get_thumbnail_image(id):
    """
    アイテムIDからサムネイル画像を取得
    """
    try:
        result = eagle_api.get_thumbnail_image(id)
        if result is None:
            raise HTTPException(status_code=404, detail="Image not found")
        
        content, content_type = result
        return Response(content=content, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/get_image")
async def get_image(id: str, ext: str = "png", max_file_size: int = 1480, quality: int = 85):
    """
    アイテムIDからオリジナル画像を取得
    - max_file_size: 最大容量をKB単位で指定。これ以上ならjpeg圧縮をかける。0なら圧縮しない
    - quality: jpeg圧縮率。0または無指定なら85を適用
    """
    try:
        # qualityが0の場合は85に設定
        if quality == 0:
            quality = 85
            
        result = eagle_api.get_image(id, ext, max_file_size, quality)
        if result is None:
            raise HTTPException(status_code=404, detail="Image not found")
        
        content, content_type = result
        return Response(content=content, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/update")
async def update_item(request: UpdateRequest):
    """
    画像情報を更新する
    """
    try:
        data = request.dict(exclude_none=True)
        result = eagle_api.update_item(data["id"], data)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/move_to_trash")
async def move_to_trash(request: MoveToTrashRequest):
    """
    指定したアイテムをゴミ箱に移動する
    """
    try:
        result = eagle_api.move_to_trash(request.itemIds)
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターをインクルード
app.include_router(auth_router, prefix="/api/auth")
app.include_router(api_router, prefix="/api/eagle")


# 静的ファイル用のハンドラー
@app.get("/assets/{file_path:path}")
async def serve_assets(file_path: str):
    file_location = os.path.join("dist/assets", file_path)
    if os.path.exists(file_location):
        return FileResponse(file_location)
    raise HTTPException(status_code=404, detail="File not found")


# SPA用のcatch-allハンドラー
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # APIパスは除外
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # 実際のファイルが存在するかチェック
    file_path = os.path.join("dist", full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Vue Routerのパスの場合はindex.htmlを返す
    return FileResponse("dist/index.html")
