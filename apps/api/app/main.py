import asyncio
import json
from http.cookies import SimpleCookie

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.api.auth import router as auth_router
from app.api.fx import router as fx_router
from app.api.notifications import router as notifications_router
from app.api.profile import router as profile_router
from app.api.public import router as public_router
from app.api.uploads import UPLOAD_DIR, router as uploads_router
from app.api.wishlists import router as wishlist_router
from app.core.config import settings
from app.db.session import engine
from app.utils.security import decode_access_token
from app.ws.manager import manager

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(fx_router)
app.include_router(notifications_router)
app.include_router(profile_router)
app.include_router(uploads_router)
app.include_router(wishlist_router)
app.include_router(public_router)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/wishlist/{public_id}")
async def wishlist_ws(websocket: WebSocket, public_id: str) -> None:
    await manager.connect(public_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(public_id, websocket)


@app.websocket("/ws/notifications")
async def notifications_ws(websocket: WebSocket) -> None:
    cookie_raw = websocket.headers.get("cookie", "")
    cookies = SimpleCookie()
    cookies.load(cookie_raw)
    token = cookies.get("access_token")
    if not token:
        await websocket.close(code=4401)
        return
    try:
        payload = decode_access_token(token.value)
        user_id = int(payload["sub"])
    except Exception:
        await websocket.close(code=4401)
        return

    room = f"user:{user_id}"
    await manager.connect(room, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(room, websocket)


async def _listen_pg_notify() -> None:
    conn: AsyncConnection = await engine.connect()
    raw = await conn.get_raw_connection()
    driver_conn = raw.driver_connection
    await driver_conn.add_listener(
        "wishlist_events",
        lambda *_args: asyncio.create_task(_notify_to_room(_args[2])),
    )
    await driver_conn.add_listener(
        "user_events",
        lambda *_args: asyncio.create_task(_notify_user_room(_args[2])),
    )
    await conn.execute(text("LISTEN wishlist_events"))
    await conn.execute(text("LISTEN user_events"))


async def _notify_to_room(payload: str) -> None:
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return
    room = event.get("wishlist_public_id")
    if room:
        await manager.broadcast(room, event)


async def _notify_user_room(payload: str) -> None:
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return
    user_id = event.get("user_id")
    if user_id is None:
        return
    await manager.broadcast(f"user:{user_id}", event)


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(_listen_pg_notify())
