import telebot
from telebot import types
import requests

# 🔑 Твой токен бота
API_TOKEN = "7988730577:AAE6aA6WWt2JL0rNk6eXrTjGn7sXLNDsnAo"
bot = telebot.TeleBot(API_TOKEN)

# 🔗 API Django
API_URL = "http://217.25.93.75/api/cars/"  # строго со слэшем!

# --- КНОПКИ ---

CATEGORY_KEYBOARD = [
    ["Седан", "Внедорожник"],
    ["Хэтчбек", "Купе"],
    ["Минивэн", "Пикап"],
    ["Универсал", "Другое"],
]

FUEL_KEYBOARD = [
    ["Бензин", "Дизель"],
    ["Газ", "Электро", "Гибрид"],
]

PRICE_KEYBOARD = [
    ["0-10000", "10000-15000"],
    ["15000-20000", "20000-30000"],
    ["30000-100000"],
]

CATEGORY_MAP = {
    "Седан": "sedan",
    "Внедорожник": "suv",
    "Хэтчбек": "hatchback",
    "Купе": "coupe",
    "Минивэн": "minivan",
    "Пикап": "pickup",
    "Универсал": "wagon",
    "Другое": "other",
}

FUEL_MAP = {
    "Бензин": "petrol",
    "Дизель": "diesel",
    "Газ": "gas",
    "Электро": "electric",
    "Гибрид": "hybrid",
}

# --- Состояния пользователей ---
user_filters = {}


def make_keyboard(buttons):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for row in buttons:
        markup.row(*row)
    return markup


# --- СТАРТ ---
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_filters[message.chat.id] = {}
    bot.send_message(
        message.chat.id,
        "Привет! 🚘 Давай подберём тебе авто.\nВыбери категорию:",
        reply_markup=make_keyboard(CATEGORY_KEYBOARD),
    )


# --- ШАГ 1: Категория ---
@bot.message_handler(func=lambda msg: msg.text in CATEGORY_MAP)
def choose_category(message):
    user_filters[message.chat.id]["category"] = message.text
    bot.send_message(
        message.chat.id,
        "Теперь выбери тип топлива:",
        reply_markup=make_keyboard(FUEL_KEYBOARD),
    )


# --- ШАГ 2: Топливо ---
@bot.message_handler(func=lambda msg: msg.text in FUEL_MAP)
def choose_fuel(message):
    user_filters[message.chat.id]["fuel"] = message.text
    bot.send_message(
        message.chat.id,
        "Укажи диапазон цены:",
        reply_markup=make_keyboard(PRICE_KEYBOARD),
    )


# --- ШАГ 3: Цена ---
@bot.message_handler(func=lambda msg: any(msg.text.startswith(x.split("-")[0]) for x in ["0-10000", "10000-15000", "15000-20000", "20000-30000", "30000-100000"]))
def choose_price(message):
    chat_id = message.chat.id
    price_range = message.text.split("-")
    min_price = int(price_range[0])
    max_price = int(price_range[1]) if len(price_range) > 1 else 100000000

    user_filters[chat_id]["price"] = (min_price, max_price)

    bot.send_message(chat_id, "🔎 Ищу авто по твоим параметрам...")

    send_filtered_cars(chat_id)


# --- Поиск авто ---
def send_filtered_cars(chat_id):
    try:
        response = requests.get(API_URL)
        cars = response.json()
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка запроса к API: {e}")
        return

    filters = user_filters.get(chat_id, {})
    results = []

    for car in cars:
        if (
            car["category"] == CATEGORY_MAP[filters["category"]]
            and car["fuel_type"] == FUEL_MAP[filters["fuel"]]
            and filters["price"][0] <= float(car["price"]) <= filters["price"][1]
        ):
            results.append(car)

    if not results:
        bot.send_message(chat_id, "🚫 Ничего не найдено по твоим параметрам.")
        return

    for car in results:
        caption = (
            f"🚗 {car['brand']} {car['model']}\n"
            f"📅 Год: {car['year']}\n"
            f"⚙️ Двигатель: {car['engine_capacity']} л\n"
            f"⛽ Топливо: {dict(FUEL_MAP.items())[[k for k,v in FUEL_MAP.items() if v==car['fuel_type']][0]]}\n"
            f"💰 Цена: {car['price']} KGS\n"
            f"📝 {car['description']}\n"
        )

        if car["image"]:
            try:
                bot.send_photo(chat_id, car["image"], caption=caption)
            except:
                bot.send_message(chat_id, caption)
        else:
            bot.send_message(chat_id, caption)


print("🤖 Бот запущен...")
bot.infinity_polling()
