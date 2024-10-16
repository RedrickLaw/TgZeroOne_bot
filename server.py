import asyncio
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable, Dict
import aiosqlite
from aiohttp import web


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
async def root(request: web.Request) -> web.Response:
    return web.Response(text=f"Placeholder")


@router.get("/api")
@handle_json_error
async def api_list_posts(request: web.Request) -> web.Response:
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
    user_id = request.match_info["user_id"]
    db = request.config_dict["DB"]
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


def get_db_path() -> Path:
    here = Path.cwd()
    while not (here / ".git").exists():
        if here == here.parent:
            raise RuntimeError("Cannot find root github dir")
        here = here.parent
    return here / "TgZeroOne_bot.db"


async def init_db(app: web.Application) -> AsyncIterator[None]:
    sqlite_db = get_db_path()
    db = await aiosqlite.connect(sqlite_db)
    db.row_factory = aiosqlite.Row
    app["DB"] = db
    yield
    await db.close()


async def init_app():
    app = web.Application()
    app.add_routes(router)
    app.cleanup_ctx.append(init_db)
    web.run_app(app)


# def try_make_db() -> None:
#     sqlite_db = get_db_path()
#     if sqlite_db.exists():
#         return

#     with sqlite3.connect(sqlite_db) as conn:
#         cur = conn.cursor()
#         cur.execute(
#             """CREATE TABLE posts (
#             id INTEGER PRIMARY KEY,
#             title TEXT,
#             text TEXT,
#             owner TEXT,
#             editor TEXT,
#             image BLOB)
#         """
#         )
#         conn.commit()


# try_make_db()

web.run_app(init_app())