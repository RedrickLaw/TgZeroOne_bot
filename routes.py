from pathlib import Path
import aiosqlite
from typing import Any, Awaitable, Callable, Dict
import asyncio

from aiohttp import web

from aiogram import Bot
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    WebAppInfo,
)
from aiogram.utils.web_app import check_webapp_signature, safe_parse_webapp_init_data

router = web.RouteTableDef()

async def fetch_user(db: aiosqlite.Connection, user_id: str) -> Dict[str, Any]:
    async with db.execute(
        "SELECT * FROM users WHERE user_id = ?", [user_id]
    ) as cursor:
        user = await cursor.fetchone()
        if user is None:
            raise RuntimeError(f"User_ID {user_id} doesn't exist")
        return {
            "user_id": user["user_id"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "username": user["username"],
            "language_code": user["language_code"],
            "is_premium": user["is_premium"],
            "is_bot": user["is_bot"],
            "added_to_attachment_menu": user["added_to_attachment_menu"],
            "created_at": user["created_at"],
            "updated_at": user["updated_at"]
        }

def handle_json_error(
    func: Callable[[web.Request], Awaitable[web.Response]]
) -> Callable[[web.Request], Awaitable[web.Response]]:
    async def handler(request: web.Request) -> web.Response:
        try:
            return await func(request)
        except asyncio.CancelledError:
            raise
        except Exception as ex:
            return web.json_response(
                {"status": "failed", "reason": str(ex)}, status=400
            )
    return handler

@router.get("/")
async def root_handler(request: web.Request):
    return web.FileResponse(Path(__file__).parent.resolve() / "index.html")

@router.get("/api")
@handle_json_error
async def api_list_users(request: web.Request) -> web.Response:
    ret = []
    db = request.config_dict["DB"]
    async with db.execute("SELECT * FROM users") as cursor:
        async for row in cursor:
            ret.append(
                {
                    "user_id": row["user_id"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "username": row["username"],
                    "language_code": row["language_code"],
                    "is_premium": row["is_premium"],
                    "is_bot": row["is_bot"],
                    "added_to_attachment_menu": row["added_to_attachment_menu"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
            )
    return web.json_response({"status": "ok", "data": ret})

@router.post("/api")
@handle_json_error
async def api_new_user(request: web.Request) -> web.Response:
    user = await request.json()
    db = request.config_dict["DB"]
    async with db.execute(
        "INSERT INTO users (user_id, first_name, last_name, username, language_code, is_premium, is_bot, added_to_attachment_menu, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [user.user_id, user.first_name, user.last_name, user.username, user.language_code, user.is_premium, user.is_bot, user.added_to_attachment_menu, user.created_at, user.updated_at]
    ) as cursor:
        user_id = cursor.lastrowid
    await db.commit()
    return web.json_response(
        {
            "status": "ok",
            "data": {
                "user_id": user["user_id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "username": user["username"],
                "language_code": user["language_code"],
                "is_premium": user["is_premium"],
                "is_bot": user["is_bot"],
                "added_to_attachment_menu": user["added_to_attachment_menu"],
                "created_at": user["created_at"],
                "updated_at": user["updated_at"]
            },
        }
    )

@router.get("/api/{user_id}")
@handle_json_error
async def api_get_user(request: web.Request) -> web.Response:
    db = request.config_dict["DB"]
    bot: Bot = request.app["bot"]
    data = await request.post()
    print(request.match_info)
    if check_webapp_signature(bot.token, data["_auth"]):
        async with db.execute(
            "SELECT * FROM game WHERE user_id = '{user_id}';"
        ) as cursor:
            user = await cursor.fetchone()
            if user is None:
                print("User_ID {user_id} doesn't exist")
                async with db.execute("INSERT INTO game (user_id) VALUES ('{user_id}');") as cursor:
                    user = cursor.fetchone()
                await db.commit()
        return web.json_response(
            {
                "status": "ok",
                "data": {
                    "user_id": user["user_id"],
                    "level": user["level"],
                    "coins": user["coins"]
                },
            }
        )
    return web.json_response({"ok": False, "err": "Unauthorized"}, status=401)

# @router.delete("/api/{user_id}")
# @handle_json_error
# async def api_del_user(request: web.Request) -> web.Response:
#     user_id = request.match_info["user_id"]
#     db = request.config_dict["DB"]
#     async with db.execute("DELETE FROM users WHERE user_id = ?", [user_id]) as cursor:
#         if cursor.rowcount == 0:
#             return web.json_response(
#                 {"status": "fail", "reason": f"post {user_id} doesn't exist"},
#                 status=404,
#             )
#     await db.commit()
#     return web.json_response({"status": "ok", "id": user_id})

@router.patch("/api/{user_id}")
@handle_json_error
async def api_update_post(request: web.Request) -> web.Response:
    user_id = request.match_info["user_id"]
    post = await request.json()
    db = request.config_dict["DB"]
    fields = {}
    if "title" in post:
        fields["title"] = post["title"]
    if "text" in post:
        fields["text"] = post["text"]
    if "editor" in post:
        fields["editor"] = post["editor"]
    if fields:
        field_names = ", ".join(f"{name} = ?" for name in fields)
        field_values = list(fields.values())
        await db.execute(
            f"UPDATE users SET {field_names} WHERE user_id = {user_id}"
        )
        await db.commit()
    user = await fetch_user(db, user_id)
    return web.json_response(
        {
            "status": "ok",
            "data": {
                "user_id": user["user_id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "username": user["username"],
                "language_code": user["language_code"],
                "is_premium": user["is_premium"],
                "is_bot": user["is_bot"],
                "added_to_attachment_menu": user["added_to_attachment_menu"],
                "created_at": user["created_at"],
                "updated_at": user["updated_at"]
            },
        }
    )

@router.post("/api/checkData")
async def check_data_handler(request: web.Request):
    bot: Bot = request.app["bot"]
    data = await request.post()
    if check_webapp_signature(bot.token, data["_auth"]):
        return web.json_response({"ok": True})
    return web.json_response({"ok": False, "err": "Unauthorized"}, status=401)

@router.post("/api/sendMessage")
async def send_message_handler(request: web.Request):
    bot: Bot = request.app["bot"]
    data = await request.post()
    try:
        web_app_init_data = safe_parse_webapp_init_data(token=bot.token, init_data=data["_auth"])
    except ValueError:
        return web.json_response({"ok": False, "err": "Unauthorized"}, status=401)

    reply_markup = None
    if data["with_webview"] == "1":
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Open",
                        web_app=WebAppInfo(
                            url=str(request.url.with_scheme("https").with_path(""))
                        ),
                    )
                ]
            ]
        )
    await bot.answer_web_app_query(
        web_app_query_id=web_app_init_data.query_id,
        result=InlineQueryResultArticle(
            id=web_app_init_data.query_id,
            title="Demo",
            input_message_content=InputTextMessageContent(
                message_text="Hello, World!",
                parse_mode=None,
            ),
            reply_markup=reply_markup,
        ),
    )
    return web.json_response({"ok": True})
