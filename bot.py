import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import requests

BOT_TOKEN = "7988730577:AAE6aA6WWt2JL0rNk6eXrTjGn7sXLNDsnAo"
API_URL = "http://127.0.0.1:8000/api/cars/"

bot = telebot.TeleBot(BOT_TOKEN)

user_state = {}  # хранение состояния {user_id: {step, filters}}

# Приветствие
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = {"step": "category", "filters": {}}

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Седан"), KeyboardButton("Внедорожник"), KeyboardButton("Минивэн"))
    bot.send_message(user_id, "Привет! Выбери категорию авто:", reply_markup=markup)

# Обработка ответов
@bot.message_handler(func=lambda msg: True)
def handle(message):
    user_id = message.chat.id
    state = user_state.get(user_id, None)

    if not state:
        bot.send_message(user_id, "Напиши /start чтобы начать заново")
        return

    step = state["step"]

    # Категория
    if step == "category":
        state["filters"]["category"] = message.text
        state["step"] = "fuel"

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Бензин", "Дизель", "Газ", "Электро")
        bot.send_message(user_id, "Выбери тип топлива:", reply_markup=markup)

    # Топливо
    elif step == "fuel":
        state["filters"]["fuel"] = message.text
        state["step"] = "price"

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("5000–10000$", "10000–15000$", "15000–20000$")
        bot.send_message(user_id, "Выбери диапазон цены:", reply_markup=markup)

    # Цена
    elif step == "price":
        state["filters"]["price"] = message.text
        state["step"] = "done"

        # Запрос к API
        filters = state["filters"]
        response = requests.get(API_URL, params=filters)
        cars = response.json()

        if cars:
            for car in cars:
                bot.send_message(
                    user_id,
                    f"🚗 {car['brand']} {car['model']}\n"
                    f"💰 Цена: {car['price']} USD\n"
                    f"📍 Категория: {car['category']}\n"
                    f"⚡ Топливо: {car['fuel']}"
                )
        else:
            bot.send_message(user_id, "❌ Авто по твоему запросу не найдено.")

        # Сбросить состояние
        user_state.pop(user_id, None)

bot.polling(none_stop=True)
