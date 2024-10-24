from pathlib import Path
import aiosqlite
from typing import Any, Awaitable, Callable, Dict
import asyncio
import json
import time

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
from aiogram.utils.deep_linking import create_start_link, decode_payload

router = web.RouteTableDef()

# async def fetch_user(db: aiosqlite.Connection, user_id: str) -> Dict[str, Any]:
#     async with db.execute(
#         "SELECT * FROM users WHERE user_id = ?", [user_id]
#     ) as cursor:
#         user = await cursor.fetchone()
#         if user is None:
#             raise RuntimeError(f"User_ID {user_id} doesn't exist")
#         return {
#             "user_id": user["user_id"],
#             "first_name": user["first_name"],
#             "last_name": user["last_name"],
#             "username": user["username"],
#             "language_code": user["language_code"],
#             "is_premium": user["is_premium"],
#             "is_bot": user["is_bot"],
#             "added_to_attachment_menu": user["added_to_attachment_menu"],
#             "created_at": user["created_at"],
#             "updated_at": user["updated_at"]
#         }
    
def calc_remaining_time(claim_time: int) -> int:
    return int(time.time()) - claim_time

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
                {"status": "failed", "description": str(ex)}, status=400
            )
    return handler

@router.get("/")
async def root_handler(request: web.Request):
    return web.FileResponse(Path(__file__).parent.resolve() / "index.html")

@router.get("/app")
@handle_json_error
async def api_get_user(request: web.Request) -> web.Response:
    db = request.config_dict["DB"]
    bot: Bot = request.app["bot"]
    if "start_param" in request.query.keys(): 
        referral_id = decode_payload(request.query["start_param"])
    else:
        referral_id = ""
    try:
        web_app_init_data = safe_parse_webapp_init_data(token=bot.token, init_data=request.query["_auth"])
    except ValueError:
        return web.json_response({"ok": False, "description": "Unauthorized"}, status=401)
    user_id = web_app_init_data.user.id
    name = web_app_init_data.user.first_name + " " + web_app_init_data.user.last_name
    async with db.execute(f"SELECT * FROM game WHERE user_id = '{user_id}';") as cursor:
        user = await cursor.fetchone()
    if user is None:
        print(f"User_ID {user_id} doesn't exist")
        await db.execute(f"INSERT INTO game (name, user_id, referral_id) VALUES ('{name}', '{user_id}', '{referral_id}');")
        await db.commit()
        async with db.execute(f"SELECT * FROM game WHERE user_id = '{referral_id}';") as cursor:
            user = await cursor.fetchone()
        await db.execute(f"UPDATE game SET coins = '{user["coins"] + 150}' WHERE user_id = '{referral_id}';")
        await db.commit()
        return web.json_response(
            {
                "status": True,
                "data": {
                    "user_id": user_id,
                    "level": 0,
                    "coins": 0,
                    "claim_time": 0 
                },
            }
        )
    async with db.execute(f"SELECT name FROM game WHERE referral_id = '{user["user_id"]}';") as cursor:
        friends_list = await cursor.fetchall()
    friends = []
    for row in friends_list:
        friends.append(row["name"])
    if calc_remaining_time(user["claim_time"]) > 15:
        claim_time = 0
    else: claim_time = calc_remaining_time(user["claim_time"])
    return web.json_response(
        {
            "status": True,
            "data": {
                "user_id": user["user_id"],
                "level": user["level"],
                "coins": user["coins"],
                "claim_time": claim_time,
                "friends": friends
            },
        }
    )

@router.get("/app/ref")
@handle_json_error
async def api_add_referral(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    try:
        web_app_init_data = safe_parse_webapp_init_data(token=bot.token, init_data=request.query_string)
    except ValueError:
        return web.json_response({"result": False, "description": "Unauthorized"}, status=401)
    link = await create_start_link(bot, web_app_init_data.user.id, encode=True)
    link = link.replace("?start", "/app?startapp")
    return web.json_response(
            {
                "status": True,
                "link": link
            }
        )

@router.patch("/app/coins")
@handle_json_error
async def api_claim_coins(request: web.Request) -> web.Response:
    data = await request.post()
    db = request.config_dict["DB"]
    bot: Bot = request.app["bot"]
    try:
        web_app_init_data = safe_parse_webapp_init_data(token=bot.token, init_data=data["_auth"])
    except ValueError:
        return web.json_response({"result": False, "description": "Unauthorized"}, status=401)
    user_id = web_app_init_data.user.id
    async with db.execute(f"SELECT * FROM game WHERE user_id = '{user_id}';") as cursor:
        user = await cursor.fetchone()
    if user is not None:
        if calc_remaining_time(user["claim_time"]) > 15:
            current_time = int(time.time())
            await db.execute(f"UPDATE game SET coins = '{user["coins"] + 100}', claim_time = {current_time} WHERE user_id = '{user_id}';")
            await db.commit()
            return web.json_response(
                {
                    "status": True,
                    "data": {
                        "coins": user["coins"] + 100,
                        "claim_time": 15
                    },
                }
            )  
        return web.json_response(
            {
                "status": True,
                "data": {
                    "coins": user["coins"],
                    "claim_time": calc_remaining_time(user["claim_time"])
                },
            }
        )  
    print(f"User_ID {user_id} doesn't exist")
    return web.json_response(
        {
            "status": True,
            "description": "User_ID {user_id} doesn't exist"
        }
    )

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
