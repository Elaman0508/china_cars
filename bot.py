import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import requests
from io import BytesIO

BOT_TOKEN = "7988730577:AAE6aA6WWt2JL0rNk6eXrTjGn7sXLNDsnAo"
API_URL = "http://217.25.93.75/api/cars/"

bot = telebot.TeleBot(BOT_TOKEN)
user_state = {}  # хранение состояния {user_id: {step, filters}}

# --- Маппинг кнопок на API ---
fuel_map = {
    "бензин": "petrol",
    "дизель": "diesel",
    "газ": "gas",
    "электро": "electric"
}

category_map = {
    "седан": "sedan",
    "внедорожник": "suv",
    "минивэн": "minivan"
}

price_map = {
    "5000–10000$": (5000, 10000),
    "10000–15000$": (10000, 15000),
    "15000–20000$": (15000, 20000)
}

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
    state = user_state.get(user_id, None)

    if not state:
        bot.send_message(user_id, "Напиши /start чтобы начать заново")
        return

    step = state["step"]

    # 1️⃣ Категория
    if step == "category":
        state["filters"]["category"] = category_map.get(message.text.lower(), message.text.lower())
        state["step"] = "fuel"

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Бензин", "Дизель", "Газ", "Электро")
        bot.send_message(user_id, "Выбери тип топлива:", reply_markup=markup)
        return

    # 2️⃣ Топливо
    if step == "fuel":
        fuel_api = fuel_map.get(message.text.lower(), message.text.lower())
        state["filters"]["fuel_type"] = fuel_api
        state["step"] = "price"

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("5000–10000$", "10000–15000$", "15000–20000$")
        bot.send_message(user_id, "Выбери диапазон цены:", reply_markup=markup)
        return

    # 3️⃣ Цена
    if step == "price":
        price_min, price_max = price_map.get(message.text, (0, 1_000_000))
        state["filters"]["price_min"] = price_min
        state["filters"]["price_max"] = price_max
        state["step"] = "done"

        # --- Получаем все машины ---
        try:
            response = requests.get(API_URL, timeout=5)
            cars = response.json()
        except Exception as e:
            bot.send_message(user_id, f"Ошибка при подключении к серверу: {e}")
            user_state.pop(user_id, None)
            return

        # --- Фильтруем в боте ---
        filtered_cars = []
        for car in cars:
            if car['category'] != state["filters"]["category"]:
                continue
            if car['fuel_type'] != state["filters"]["fuel_type"]:
                continue
            if not (price_min <= float(car['price']) <= price_max):
                continue
            filtered_cars.append(car)

        # --- Отправка пользователю ---
        if filtered_cars:
            for car in filtered_cars:
                caption = (
                    f"🚗 {car['brand']} {car['model']}\n"
                    f"💰 Цена: {car['price']} $\n"
                    f"📍 Категория: {car['category']}\n"
                    f"⚡ Топливо: {car['fuel_type']}\n"
                    f"📝 {car.get('description', '')}"
                )
                if car.get("image"):
                    try:
                        # Загружаем фото через requests и отправляем как файл
                        response = requests.get(car["image"])
                        photo = BytesIO(response.content)
                        bot.send_photo(user_id, photo, caption=caption)
                    except Exception as e:
                        bot.send_message(user_id, f"Ошибка при загрузке фото: {e}\n{caption}")
                else:
                    bot.send_message(user_id, caption)
        else:
            bot.send_message(user_id, "❌ Авто по твоему запросу не найдено.")

        # --- Сброс состояния ---
        user_state.pop(user_id, None)

bot.polling(none_stop=True)
