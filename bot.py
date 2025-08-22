import aiohttp
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

API_TOKEN = "ТВОЙ_ТОКЕН_БОТА"
API_URL = "http://217.25.93.75/api/cars/"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Команда /start
@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🚘 Показать машины", callback_data="show_cars")]
        ]
    )
    await message.answer("Привет! Нажми кнопку, чтобы посмотреть машины 🚗", reply_markup=keyboard)


# Обработка кнопки
@dp.callback_query()
async def show_cars(callback: types.CallbackQuery):
    if callback.data == "show_cars":
        await callback.answer("Загружаю список машин...")

        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as response:
                if response.status == 200:
                    cars = await response.json()

                    if cars:
                        for car in cars:
                            text = (
                                f"🚗 {car['brand']} {car['model']}\n"
                                f"💰 Цена: {car['price']} KGS\n"
                                f"📍 Город: {car['city']}\n"
                                f"📝 {car['description']}"
                            )

                            photo_url = car.get("image")
                            if photo_url:
                                try:
                                    await bot.send_photo(
                                        chat_id=callback.from_user.id,
                                        photo=photo_url,
                                        caption=text
                                    )
                                except Exception as e:
                                    await bot.send_message(callback.from_user.id, f"{text}\n❌ Ошибка фото: {e}")
                            else:
                                await bot.send_message(callback.from_user.id, text)
                    else:
                        await bot.send_message(callback.from_user.id, "Машин пока нет 🚫")
                else:
                    await bot.send_message(callback.from_user.id, "Ошибка API 🚨")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
