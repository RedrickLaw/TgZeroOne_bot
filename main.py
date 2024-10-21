import logging, os, sys

from database import init_db
from dotenv import find_dotenv, load_dotenv
from aiohttp.web import run_app
from aiohttp.web_app import Application
from handlers import my_router
from routes import router

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import MenuButtonWebApp, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

load_dotenv(find_dotenv('.env'))
TOKEN = os.environ.get("token")
APP_BASE_URL = os.environ.get("APP_BASE_URL")

async def on_startup(bot: Bot, base_url: str):
    await bot.set_webhook(f"{base_url}/webhook")
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="Play!", web_app=WebAppInfo(url=f"{base_url}"))
    )

def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher["base_url"] = APP_BASE_URL
    dispatcher.startup.register(on_startup)
    dispatcher.include_router(my_router)
    app = Application()
    app["bot"] = bot
    app.cleanup_ctx.append(init_db)
    app.add_routes(router)
    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
    ).register(app, path="/webhook")
    setup_application(app, dispatcher, bot=bot)

    run_app(app, host="127.0.0.1", port=8081)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
