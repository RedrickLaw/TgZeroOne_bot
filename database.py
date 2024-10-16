from pathlib import Path
from typing import AsyncIterator
import aiosqlite
from aiohttp.web_app import Application

def get_db_path() -> Path:
    here = Path.cwd()
    while not (here / ".git").exists():
        if here == here.parent:
            raise RuntimeError("Cannot find root github dir")
        here = here.parent
    return here / "TgZeroOne_bot.db"

async def init_db(app: Application) -> AsyncIterator[None]:
    sqlite_db = get_db_path()
    db = await aiosqlite.connect(sqlite_db)
    db.row_factory = aiosqlite.Row
    app["DB"] = db
    yield
    await db.close()