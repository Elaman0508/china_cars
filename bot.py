import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import requests

BOT_TOKEN = "7988730577:AAE6aA6WWt2JL0rNk6eXrTjGn7sXLNDsnAo"
API_URL = "http://217.25.93.75/api/cars/"  # продакшн URL через Nginx

bot = telebot.TeleBot(BOT_TOKEN)
user_state = {}  # хранение состояния {user_id: {step, filters}}

# Соответствие кнопок значениям модели
CATEGORY_MAP = {"Седан": "sedan", "Внедорожник": "suv", "Минивэн": "minivan"}
FUEL_MAP = {"Бензин": "petrol", "Дизель": "diesel", "Газ": "gas", "Электро": "electric"}

# --- Приветствие ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = {"step": "category", "filters": {}}

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Седан"), KeyboardButton("Внедорожник"), KeyboardButton("Минивэн"))
    bot.send_message(user_id, "Привет! Выбери категорию авто:", reply_markup=markup)

# --- Обработка ответов ---
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
        selected = CATEGORY_MAP.get(message.text)
        if not selected:
            bot.send_message(user_id, "Пожалуйста, выбери категорию с кнопок.")
            return

        state["filters"]["category"] = selected
        state["step"] = "fuel"

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Бензин", "Дизель", "Газ", "Электро")
        bot.send_message(user_id, "Выбери тип топлива:", reply_markup=markup)
        return

    # 2️⃣ Топливо
    if step == "fuel":
        selected = FUEL_MAP.get(message.text)
        if not selected:
            bot.send_message(user_id, "Пожалуйста, выбери тип топлива с кнопок.")
            return

        state["filters"]["fuel_type"] = selected
        state["step"] = "price"

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("5000–10000$", "10000–15000$", "15000–20000$")
        bot.send_message(user_id, "Выбери диапазон цены:", reply_markup=markup)
        return

    # 3️⃣ Цена
    if step == "price":
        try:
            price_range = message.text.replace("$", "").split("–")
            state["filters"]["price_min"] = price_range[0]
            state["filters"]["price_max"] = price_range[1]
        except Exception:
            bot.send_message(user_id, "Неверный формат цены. Выбери диапазон с кнопок.")
            return

        state["step"] = "done"
        filters = state["filters"]

        # --- Запрос к API ---
        try:
            response = requests.get(API_URL, params=filters, timeout=5)
            response.raise_for_status()
            cars = response.json()
        except Exception as e:
            bot.send_message(user_id, f"Ошибка при подключении к серверу: {e}")
            user_state.pop(user_id, None)
            return

        # --- Отправка результатов ---
        if cars:
            for car in cars:
                caption = (
                    f"🚗 {car['brand']} {car['model']} ({car['year']})\n"
                    f"💰 Цена: {car['price']} $\n"
                    f"📍 Категория: {car['category']}\n"
                    f"⚡ Топливо: {car['fuel_type']}"
                )
                # Фото через прямой URL
                if car.get("image"):
                    bot.send_photo(user_id, car["image"], caption=caption)
                else:
                    bot.send_message(user_id, caption)
        else:
            bot.send_message(user_id, "❌ Авто по твоему запросу не найдено.")

        # Сброс состояния
        user_state.pop(user_id, None)

# --- Запуск бота ---
bot.polling(none_stop=True)
