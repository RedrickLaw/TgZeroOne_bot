import config
from database import SQLighter
import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import KeyboardButton, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums.content_type import ContentType
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode

# Логирование
logging.basicConfig(level=logging.INFO)
# Обработка базы

db = SQLighter(config.database_name)
print(db.select_single("test1")[1])
if db.select_single("test1")[1] != "test1":
   db.insert_new("'test1'", "'redricklaw'", 220)
# Обработка бота
bot = Bot(token=config.token)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    webAppInfo = types.WebAppInfo(url="https://redricklaw.github.io/TgZeroOne_bot/")
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text='Play!', web_app=webAppInfo))
    
    await message.answer(text='Привет!', reply_markup=builder.as_markup())

@dp.message(F.content_type == ContentType.WEB_APP_DATA)
async def parse_data(message: types.Message):
    data = json.loads(message.web_app_data.data)
    await message.answer(f'<b>{data["title"]}</b>\n\n<code>{data["desc"]}</code>\n\n{data["text"]}', parse_mode=ParseMode.HTML)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    
db.close()
if __name__ == "__main__":
   asyncio.run(main())