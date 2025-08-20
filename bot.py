import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

API_TOKEN = "7988730577:AAE6aA6WWt2JL0rNk6eXrTjGn7sXLNDsnAo"
API_URL = "http://127.0.0.1:8000/api/cars/"  # меняй на свой сервер

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 📌 Кнопка "Список машин"
@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚘 Показать машины", callback_data="show_cars")]
    ])
    await message.answer("Привет! Я бот-магазин машин 🚗", reply_markup=keyboard)

# 📌 Получение списка машин
@dp.callback_query(lambda c: c.data == "show_cars")
async def show_cars(callback: types.CallbackQuery):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as resp:
            cars = await resp.json()

    if not cars:
        await callback.message.answer("Пока нет машин в базе ❌")
        return

    for car in cars:
        caption = f"""
🚗 {car['brand']} {car['model']}
💰 Цена: {car['price']} KGS
📍 Город: {car['city']}
📝 {car['description']}
"""
        # ✅ теперь фото по URL
        await callback.message.answer_photo(photo=car["image"], caption=caption)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
