import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import requests
import os

BOT_TOKEN = "7988730577:AAE6aA6WWt2JL0rNk6eXrTjGn7sXLNDsnAo"
API_URL = "http://217.25.93.75/api/cars/"
MEDIA_PATH = "/var/www/china_cars/media/cars/"  # путь к локальным фото

bot = telebot.TeleBot(BOT_TOKEN)
user_state = {}  # {user_id: {"step": ..., "filters": {...}}}

# --- /start ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = {"step": "category", "filters": {}}

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("sedan", "suv", "hatchback", "minivan")
    bot.send_message(user_id, "Привет! Выбери категорию авто:", reply_markup=markup)

# --- обработка сообщений ---
@bot.message_handler(func=lambda msg: True)
def handle(message):
    user_id = message.chat.id
    state = user_state.get(user_id)
    if not state:
        bot.send_message(user_id, "Напиши /start чтобы начать заново")
        return

    step = state["step"]

    # 1️⃣ Категория
    if step == "category":
        state["filters"]["category"] = message.text.lower()
        state["step"] = "fuel"

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("petrol", "diesel", "gas", "electric")
        bot.send_message(user_id, "Выбери тип топлива:", reply_markup=markup)
        return

    # 2️⃣ Топливо
    if step == "fuel":
        state["filters"]["fuel_type"] = message.text.lower()
        state["step"] = "color"

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Красный", "Синий", "Черный", "Белый")
        bot.send_message(user_id, "Выбери цвет авто:", reply_markup=markup)
        return

    # 3️⃣ Цвет
    if step == "color":
        state["filters"]["color"] = message.text.lower()
        state["step"] = "condition"

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Новый", "Б/У")
        bot.send_message(user_id, "Выбери состояние авто:", reply_markup=markup)
        return

    # 4️⃣ Состояние
    if step == "condition":
        state["filters"]["condition"] = "new" if message.text.lower() == "новый" else "used"
        state["step"] = "price"

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("5000–10000", "10000–15000", "15000–20000")
        bot.send_message(user_id, "Выбери диапазон цены (KGS):", reply_markup=markup)
        return

    # 5️⃣ Цена
    if step == "price":
        state["filters"]["price"] = message.text
        state["step"] = "done"

        price_range = state["filters"]["price"].split("–")
        filters = state["filters"]
        filters["price_min"] = price_range[0]
        filters["price_max"] = price_range[1]
        filters.pop("price")

        try:
            response = requests.get(API_URL, params=filters, timeout=10)
            response.raise_for_status()
            cars = response.json()
        except Exception as e:
            bot.send_message(user_id, f"❌ Ошибка запроса к API: {e}")
            user_state.pop(user_id, None)
            return

        if cars:
            for car in cars:
                caption = (
                    f"🚗 {car['brand']} {car['model']}\n"
                    f"📅 Год: {car['year']}\n"
                    f"⚙️ Двигатель: {car['engine_capacity']} л\n"
                    f"⛽ Топливо: {car['fuel_type']}\n"
                    f"🎨 Цвет: {car.get('color', '—')}\n"
                    f"📌 Состояние: {'Новый' if car.get('condition')=='new' else 'Б/У'}\n"
                    f"💰 Цена: {car['price']} KGS\n"
                    f"📝 {car['description']}"
                )

                # --- отправка фото локально ---
                if car.get("image"):
                    filename = os.path.basename(car["image"])
                    file_path = os.path.join(MEDIA_PATH, filename)
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            bot.send_photo(user_id, f, caption=caption)
                    else:
                        # fallback: по публичной ссылке
                        try:
                            bot.send_photo(user_id, car["image"], caption=caption)
                        except:
                            bot.send_message(user_id, f"⚠️ Фото не найдено.\n{caption}")
                else:
                    bot.send_message(user_id, caption)
        else:
            bot.send_message(user_id, "❌ Авто по твоему запросу не найдено.")

        # сброс состояния
        user_state.pop(user_id, None)

bot.polling(none_stop=True)
