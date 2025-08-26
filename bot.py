import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import requests
import os

BOT_TOKEN = "7988730577:AAE6aA6WWt2JL0rNk6eXrTjGn7sXLNDsnAo"
API_URL = "http://217.25.93.75/api/cars/"
MEDIA_PATH = "/var/www/china_cars/media/cars/"

bot = telebot.TeleBot(BOT_TOKEN)
user_state = {}   # {user_id: {"step": ..., "filters": {...}, "cars": [...], "index": 0}}
favorites = {}    # {user_id: [car, car, ...]}

# --- маппинги ---
FUEL_MAP = {"petrol": "petrol", "diesel": "diesel", "gas": "gas", "electric": "electric"}
COLOR_MAP = {"Красный": "red", "Синий": "blue", "Черный": "black", "Белый": "white"}
COND_MAP = {"Новый": "new", "Б/У": "used"}
PRICE_MAP = {"5000–10000": (5000, 10000), "10000–15000": (10000, 15000), "15000–20000": (15000, 20000)}

# --- /start ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = {"step": "category", "filters": {}}

    markup = InlineKeyboardMarkup()
    for cat in ["sedan", "suv", "hatchback", "minivan"]:
        markup.add(InlineKeyboardButton(cat, callback_data=f"category:{cat}"))

    bot.send_message(user_id, "Привет! Выбери категорию авто:", reply_markup=markup)


# --- /favorites ---
@bot.message_handler(commands=['favorites'])
def show_favorites(message):
    user_id = message.chat.id
    user_favs = favorites.get(user_id, [])

    if not user_favs:
        bot.send_message(user_id, "⭐ У тебя пока нет избранных машин.")
        return

    bot.send_message(user_id, f"⭐ Твои избранные авто ({len(user_favs)}):")

    for car in user_favs:
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

        if car.get("image"):
            filename = os.path.basename(car["image"])
            file_path = os.path.join(MEDIA_PATH, filename)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    bot.send_photo(user_id, f, caption=caption)
            else:
                bot.send_photo(user_id, car["image"], caption=caption)
        else:
            bot.send_message(user_id, caption)


# --- обработка callback ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.message.chat.id
    state = user_state.get(user_id)
    if not state:
        bot.send_message(user_id, "Напиши /start чтобы начать заново")
        return

    step = state["step"]

    # 1️⃣ Категория
    if call.data.startswith("category:") and step == "category":
        category = call.data.split(":")[1]
        state["filters"]["category"] = category
        state["step"] = "fuel"

        markup = InlineKeyboardMarkup()
        for f in FUEL_MAP:
            markup.add(InlineKeyboardButton(f, callback_data=f"fuel:{f}"))
        bot.edit_message_text("Выбери тип топлива:", user_id, call.message.id, reply_markup=markup)

    # 2️⃣ Топливо
    elif call.data.startswith("fuel:") and step == "fuel":
        fuel = call.data.split(":")[1]
        state["filters"]["fuel_type"] = FUEL_MAP[fuel]
        state["step"] = "color"

        markup = InlineKeyboardMarkup()
        for c in COLOR_MAP:
            markup.add(InlineKeyboardButton(c, callback_data=f"color:{c}"))
        bot.edit_message_text("Выбери цвет авто:", user_id, call.message.id, reply_markup=markup)

    # 3️⃣ Цвет
    elif call.data.startswith("color:") and step == "color":
        color = call.data.split(":")[1]
        state["filters"]["color"] = COLOR_MAP[color]
        state["step"] = "condition"

        markup = InlineKeyboardMarkup()
        for c in COND_MAP:
            markup.add(InlineKeyboardButton(c, callback_data=f"condition:{c}"))
        bot.edit_message_text("Выбери состояние авто:", user_id, call.message.id, reply_markup=markup)

    # 4️⃣ Состояние
    elif call.data.startswith("condition:") and step == "condition":
        cond = call.data.split(":")[1]
        state["filters"]["condition"] = COND_MAP[cond]
        state["step"] = "price"

        markup = InlineKeyboardMarkup()
        for p in PRICE_MAP:
            markup.add(InlineKeyboardButton(p, callback_data=f"price:{p}"))
        bot.edit_message_text("Выбери диапазон цены (KGS):", user_id, call.message.id, reply_markup=markup)

    # 5️⃣ Цена → выдача
    elif call.data.startswith("price:") and step == "price":
        price = call.data.split(":")[1]
        price_min, price_max = PRICE_MAP[price]
        state["filters"]["price_min"] = price_min
        state["filters"]["price_max"] = price_max
        state["step"] = "done"

        try:
            response = requests.get(API_URL, params=state["filters"], timeout=10)
            response.raise_for_status()
            state["cars"] = response.json()
            state["index"] = 0
        except Exception as e:
            bot.edit_message_text(f"❌ Ошибка API: {e}", user_id, call.message.id)
            user_state.pop(user_id, None)
            return

        if state["cars"]:
            show_car(user_id, call.message.id)
        else:
            bot.edit_message_text("❌ Авто не найдено.", user_id, call.message.id)
            user_state.pop(user_id, None)

    # 📲 Пагинация
    elif call.data in ["prev", "next"]:
        if "cars" not in state: return
        if call.data == "prev" and state["index"] > 0:
            state["index"] -= 1
        elif call.data == "next" and state["index"] < len(state["cars"]) - 1:
            state["index"] += 1
        show_car(user_id, call.message.id)

    # ⭐ Добавление в избранное
    elif call.data == "favorite":
        car = state["cars"][state["index"]]
        fav_list = favorites.setdefault(user_id, [])
        if car not in fav_list:  # чтобы не дублировались
            fav_list.append(car)
            bot.answer_callback_query(call.id, "⭐ Добавлено в избранное!")
        else:
            bot.answer_callback_query(call.id, "Уже в избранном ✅")


# --- функция показа машины ---
def show_car(user_id, message_id):
    state = user_state[user_id]
    car = state["cars"][state["index"]]

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

    # inline-кнопки навигации
    markup = InlineKeyboardMarkup()
    if state["index"] > 0:
        markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="prev"))
    if state["index"] < len(state["cars"]) - 1:
        markup.add(InlineKeyboardButton("➡️ Вперёд", callback_data="next"))
    markup.add(InlineKeyboardButton("⭐ В избранное", callback_data="favorite"))

    # фото
    if car.get("image"):
        filename = os.path.basename(car["image"])
        file_path = os.path.join(MEDIA_PATH, filename)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                bot.edit_message_media(
                    media=InputMediaPhoto(f, caption=caption),
                    chat_id=user_id,
                    message_id=message_id,
                    reply_markup=markup
                )
        else:
            bot.edit_message_caption(
                caption=caption,
                chat_id=user_id,
                message_id=message_id,
                reply_markup=markup
            )
    else:
        bot.edit_message_caption(
            caption=caption,
            chat_id=user_id,
            message_id=message_id,
            reply_markup=markup
        )


bot.polling(none_stop=True)
