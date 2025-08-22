import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

API_TOKEN = "7988730577:AAE6aA6WWt2JL0rNk6eXrTjGn7sXLNDsnAo"
API_URL = "http://217.25.93.75/api/cars/"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Команда /start
@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🚘 Показать машины", callback_data="show_cars")]
    ])
    await message.answer("Привет! Я бот-магазин машин 🚗", reply_markup=keyboard)

# Обработка нажатия кнопки "Показать машины"
@dp.callback_query(lambda c: c.data == "show_cars")
async def show_cars(callback: types.CallbackQuery):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as resp:
            try:
                cars = await resp.json()
            except Exception:
                await callback.message.answer("❌ Ошибка при получении данных с сервера")
                return

    if not cars:
        await callback.message.answer("Пока нет машин в базе ❌")
        return

    for car in cars:
        caption = f"""
🚗 {car.get('brand','')} {car.get('model','')}
💰 Цена: {car.get('price','')} KGS
📍 Город: {car.get('city','')}
📝 {car.get('description','')}
"""
        image_url = car.get("image", "")
        if image_url and not image_url.startswith("http"):
            image_url = f"http://217.25.93.75:8080{image_url}"

        try:
            if image_url:
                # Скачиваем картинку в память и отправляем как файл
                async with aiohttp.ClientSession() as img_session:
                    async with img_session.get(image_url) as img_resp:
                        if img_resp.status == 200:
                            content = await img_resp.read()
                            file = BufferedInputFile(content, filename="car.png")
                            await callback.message.answer_photo(photo=file, caption=caption)
                        else:
                            await callback.message.answer(f"{caption}\n❌ Фото недоступно")
            else:
                await callback.message.answer(f"{caption}\n❌ Фото недоступно")
        except Exception as e:
            await callback.message.answer(f"{caption}\n❌ Ошибка при отправке фото: {e}")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
