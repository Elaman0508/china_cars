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

    # добавим кнопку "⭐ Избранные"
    markup.add(InlineKeyboardButton("⭐ Избранные", callback_data="show_favorites"))

    bot.send_message(user_id, "Привет! Выбери категорию авто:", reply_markup=markup)


# --- /favorites ---
@bot.message_handler(commands=['favorites'])
def show_favorites(message):
    send_favorites(message.chat.id)


# --- вынесенная функция показа избранных ---
def send_favorites(user_id):
    user_favs = favorites.get(user_id, [])

    if not user_favs:
        bot.send_message(user_id, "⭐ У тебя пока нет избранных машин.")
        return

    bot.send_message(user_id, f"⭐ Твои избранные авто ({len(user_favs)}):")

    for idx, car in enumerate(user_favs):
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

        # кнопка удаления
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🗑 Удалить", callback_data=f"del_fav:{idx}"))

        if car.get("image"):
            filename = os.path.basename(car["image"])
            file_path = os.path.join(MEDIA_PATH, filename)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    bot.send_photo(user_id, f, caption=caption, reply_markup=markup)
            else:
                bot.send_photo(user_id, car["image"], caption=caption, reply_markup=markup)
        else:
            bot.send_message(user_id, caption, reply_markup=markup)


# --- обработка callback ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.message.chat.id
    state = user_state.get(user_id)

    # ⭐ открыть избранное из меню
    if call.data == "show_favorites":
        send_favorites(user_id)
        bot.answer_callback_query(call.id)
        return

    # 🗑 удалить из избранного
    if call.data.startswith("del_fav:"):
        idx = int(call.data.split(":")[1])
        if user_id in favorites and idx < len(favorites[user_id]):
            removed = favorites[user_id].pop(idx)
            bot.answer_callback_query(call.id, f"🗑 {removed['brand']} {removed['model']} удалён")
            bot.delete_message(user_id, call.message.id)  # удаляем карточку из чата
        return

    if not state:
        bot.send_message(user_id, "Напиши /start чтобы начать заново")
        return

    step = state["step"]

    # ... 👇 всё как у тебя было (category, fuel, color, condition, price, prev/next, favorite) ...


    # ⭐ Добавление в избранное
    if call.data == "favorite":
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

    # Сначала уберём старую клавиатуру (чтобы не висели кнопки цен)
    try:
        bot.edit_message_reply_markup(chat_id=user_id, message_id=message_id, reply_markup=None)
    except:
        pass

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
