import asyncio, logging, json, server, os
from dotenv import find_dotenv, load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums.content_type import ContentType
from aiogram.filters import Command
from aiogram.enums.parse_mode import ParseMode

# Логирование
logging.basicConfig(level=logging.INFO)

# Получение переменных окружения 
load_dotenv(find_dotenv('config.env'))
TOKEN = os.environ.get("token")

# Обработка бота
bot = Bot(token=TOKEN)
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
   await server.start_server()
    
if __name__ == "__main__":
   asyncio.run(main())