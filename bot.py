import asyncio
import aiohttp
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

API_TOKEN = "7988730577:AAE6aA6WWt2JL0rNk6eXrTjGn7sXLNDsnAo"
API_URL = "http://217.25.93.75:8080/api/cars/"  # твой сервер
TEMP_IMAGE = "temp_car.png"  # временный файл для скачивания

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🚘 Показать машины", callback_data="show_cars")]
    ])
    await message.answer("Привет! Я бот-магазин машин 🚗", reply_markup=keyboard)

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
    🚗 {car.get('brand', '')} {car.get('model', '')}
    💰 Цена: {car.get('price', '')} KGS
    📍 Город: {car.get('city', '')}
    📝 {car.get('description', '')}
    """
        image_url = car.get("image", "")

        if image_url and not image_url.startswith("http"):
            image_url = f"http://217.25.93.75:8080{image_url}"

        try:
            if image_url:
                # ✅ Просто передаём URL
                await callback.message.answer_photo(photo=image_url, caption=caption)
            else:
                await callback.message.answer(f"{caption}\n❌ Фото недоступно")
        except Exception as e:
            await callback.message.answer(f"{caption}\n❌ Ошибка при отправке фото: {e}")


    # Удаляем временный файл после всех сообщений
    if os.path.exists(TEMP_IMAGE):
        os.remove(TEMP_IMAGE)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
