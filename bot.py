import telebot
import requests
from io import BytesIO

TOKEN = "7988730577:AAE6aA6WWt2JL0rNk6eXrTjGn7sXLNDsnAo"
API_URL = "http://217.25.93.75/api/cars/"

bot = telebot.TeleBot(TOKEN)

# ====== Фильтры ======
user_filters = {}

CATEGORIES = ["Легковые", "Грузовые", "Автобусы"]
FUEL_TYPES = ["Бензин", "Газ", "Дизель"]
PRICE_RANGES = {
    "10-15 тыс": (10000, 15000),
    "15-20 тыс": (15000, 20000),
    "20-30 тыс": (20000, 30000)
}


# ====== Старт ======
@bot.message_handler(commands=["start"])
def start(message):
    user_filters[message.chat.id] = {}
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for c in CATEGORIES:
        markup.add(c)
    bot.send_message(message.chat.id, "👋 Привет! Выберите категорию:", reply_markup=markup)


# ====== Выбор категории ======
@bot.message_handler(func=lambda m: m.text in CATEGORIES)
def choose_category(message):
    user_filters[message.chat.id]["category"] = message.text
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for f in FUEL_TYPES:
        markup.add(f)
    bot.send_message(message.chat.id, "⛽ Теперь выберите топливо:", reply_markup=markup)


# ====== Выбор топлива ======
@bot.message_handler(func=lambda m: m.text in FUEL_TYPES)
def choose_fuel(message):
    user_filters[message.chat.id]["fuel"] = message.text
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for p in PRICE_RANGES.keys():
        markup.add(p)
    bot.send_message(message.chat.id, "💰 Теперь выберите диапазон цены:", reply_markup=markup)


# ====== Выбор цены ======
@bot.message_handler(func=lambda m: m.text in PRICE_RANGES.keys())
def choose_price(message):
    user_filters[message.chat.id]["price"] = message.text
    send_filtered_cars(message.chat.id)


# ====== Получение и отправка авто ======
def send_filtered_cars(user_id):
    filters = user_filters.get(user_id, {})
    bot.send_message(user_id, "🔎 Ищу подходящие авто...")

    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        cars = response.json()
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка получения данных: {e}")
        return

    min_p, max_p = PRICE_RANGES[filters["price"]]

    results = []
    for car in cars:
        if (
            car.get("category") == filters["category"]
            and car.get("fuel") == filters["fuel"]
            and min_p <= float(car.get("price", 0)) <= max_p
        ):
            results.append(car)

    if not results:
        bot.send_message(user_id, "🚫 Авто по вашему фильтру не найдено")
        return

    for car in results:
        caption = (
            f"🚗 {car.get('brand', '')} {car.get('model', '')}\n"
            f"💰 Цена: {car.get('price', '')} KGS\n"
            f"📍 Город: {car.get('city', '')}\n"
            f"📝 {car.get('description', '')}"
        )

        if car.get("image"):
            try:
                resp = requests.get(car["image"], timeout=5)
                if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
                    photo = BytesIO(resp.content)
                    photo.seek(0)
                    bot.send_photo(user_id, photo, caption=caption)
                else:
                    bot.send_message(user_id, f"❌ Фото недоступно\n{caption}")
            except Exception as e:
                bot.send_message(user_id, f"❌ Ошибка загрузки фото: {e}\n{caption}")
        else:
            bot.send_message(user_id, caption)


# ====== Запуск ======
print("🤖 Бот запущен...")
bot.polling(none_stop=True)
