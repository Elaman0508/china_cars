import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto, ReplyKeyboardRemove
)
import requests
import os

BOT_TOKEN = "7988730577:AAE6aA6WWt2JL0rNk6eXrTjGn7sXLNDsnAo"
API_URL = "http://217.25.93.75/api/cars/"
MEDIA_PATH = "/var/www/china_cars/media/cars/"

bot = telebot.TeleBot(BOT_TOKEN)

# user_state[user_id] = {
#   "step": str,
#   "filters": dict,
#   "cars": list,
#   "index": int,
#   "msg_id": int,        # id сообщения с карточкой
# }
user_state = {}
favorites = {}  # {user_id: [car, ...]}

# --- маппинги ---
FUEL_MAP = {"petrol": "petrol", "diesel": "diesel", "gas": "gas", "electric": "electric"}
COLOR_MAP = {"Красный": "red", "Синий": "blue", "Черный": "black", "Белый": "white"}
COND_MAP  = {"Новый": "new", "Б/У": "used"}
PRICE_MAP = {"5000–10000": (5000, 10000), "10000–15000": (10000, 15000), "15000–20000": (15000, 20000)}

# -------------------- helpers --------------------
def car_caption(car: dict) -> str:
    return (
        f"🚗 {car['brand']} {car['model']}\n"
        f"📅 Год: {car['year']}\n"
        f"⚙️ Двигатель: {car['engine_capacity']} л\n"
        f"⛽ Топливо: {car['fuel_type']}\n"
        f"🎨 Цвет: {car.get('color', '—')}\n"
        f"📌 Состояние: {'Новый' if car.get('condition') == 'new' else 'Б/У'}\n"
        f"💰 Цена: {car['price']} KGS\n"
        f"📝 {car['description']}"
    )

def nav_markup(state) -> InlineKeyboardMarkup:
    m = InlineKeyboardMarkup()
    if state["index"] > 0:
        m.add(InlineKeyboardButton("⬅️ Назад", callback_data="prev"))
    if state["index"] < len(state["cars"]) - 1:
        m.add(InlineKeyboardButton("➡️ Вперёд", callback_data="next"))
    m.add(InlineKeyboardButton("⭐ В избранное", callback_data="favorite"))
    return m

def send_car_message(user_id: int) -> None:
    """Отправляет НОВОЕ сообщение с текущей машиной и запоминает msg_id."""
    st = user_state[user_id]
    car = st["cars"][st["index"]]
    caption = car_caption(car)
    markup = nav_markup(st)

    # Пытаемся отправить фото, иначе текст
    if car.get("image"):
        filename = os.path.basename(car["image"])
        file_path = os.path.join(MEDIA_PATH, filename)
        try:
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    msg = bot.send_photo(user_id, f, caption=caption, reply_markup=markup)
            else:
                msg = bot.send_photo(user_id, car["image"], caption=caption, reply_markup=markup)
            st["msg_id"] = msg.message_id
            return
        except Exception:
            pass  # упадём в текст

    msg = bot.send_message(user_id, caption, reply_markup=markup)
    st["msg_id"] = msg.message_id

def update_car_message(user_id: int) -> None:
    """Обновляет существующее сообщение: меняет фото/подпись. При несовместимости – шлёт новое и удаляет старое."""
    st = user_state[user_id]
    car = st["cars"][st["index"]]
    caption = car_caption(car)
    markup = nav_markup(st)
    msg_id = st.get("msg_id")

    # если нет id сообщения – просто отправим новое
    if not msg_id:
        send_car_message(user_id)
        return

    # Пытаемся редактировать media (если фото есть)
    if car.get("image"):
        filename = os.path.basename(car["image"])
        file_path = os.path.join(MEDIA_PATH, filename)
        try:
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    bot.edit_message_media(
                        media=InputMediaPhoto(f, caption=caption),
                        chat_id=user_id,
                        message_id=msg_id,
                        reply_markup=markup
                    )
            else:
                bot.edit_message_media(
                    media=InputMediaPhoto(car["image"], caption=caption),
                    chat_id=user_id,
                    message_id=msg_id,
                    reply_markup=markup
                )
            return
        except Exception:
            # не смогли отредактировать (например, предыдущее сообщение было текстом) — отправим новое
            try:
                bot.delete_message(user_id, msg_id)
            except Exception:
                pass
            send_car_message(user_id)
            return

    # Если у текущего авто нет фото: редактируем только подпись (если предыдущее сообщение было фото или текст с caption)
    try:
        bot.edit_message_caption(
            caption=caption,
            chat_id=user_id,
            message_id=msg_id,
            reply_markup=markup
        )
    except Exception:
        # если и это нельзя – шлём новое и удаляем старое
        try:
            bot.delete_message(user_id, msg_id)
        except Exception:
            pass
        send_car_message(user_id)

# -------------------- commands --------------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = {"step": "category", "filters": {}}

    # На всякий случай убираем старые Reply-клавы (если остались от старого кода)
    try:
        bot.send_message(user_id, "Обновляю меню…", reply_markup=ReplyKeyboardRemove())
    except Exception:
        pass

    markup = InlineKeyboardMarkup()
    for cat in ["sedan", "suv", "hatchback", "minivan"]:
        markup.add(InlineKeyboardButton(cat, callback_data=f"category:{cat}"))
    markup.add(InlineKeyboardButton("⭐ Избранные", callback_data="show_favorites"))

    bot.send_message(user_id, "Привет! Выбери категорию авто:", reply_markup=markup)

@bot.message_handler(commands=['favorites'])
def favorites_cmd(message):
    send_favorites(message.chat.id)

# -------------------- favorites --------------------
def send_favorites(user_id: int):
    user_favs = favorites.get(user_id, [])
    if not user_favs:
        bot.send_message(user_id, "⭐ У тебя пока нет избранных машин.")
        return

    bot.send_message(user_id, f"⭐ Твои избранные авто ({len(user_favs)}):")
    for idx, car in enumerate(user_favs):
        caption = car_caption(car)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🗑 Удалить", callback_data=f"del_fav:{idx}"))

        if car.get("image"):
            filename = os.path.basename(car["image"])
            file_path = os.path.join(MEDIA_PATH, filename)
            try:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        bot.send_photo(user_id, f, caption=caption, reply_markup=markup)
                else:
                    bot.send_photo(user_id, car["image"], caption=caption, reply_markup=markup)
                continue
            except Exception:
                pass
        bot.send_message(user_id, caption, reply_markup=markup)

# -------------------- callbacks --------------------
@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    user_id = call.message.chat.id
    state = user_state.get(user_id)

    # открыть избранное из меню
    if call.data == "show_favorites":
        send_favorites(user_id)
        bot.answer_callback_query(call.id)
        return

    # удаление из избранного
    if call.data.startswith("del_fav:"):
        idx = int(call.data.split(":")[1])
        if user_id in favorites and 0 <= idx < len(favorites[user_id]):
            removed = favorites[user_id].pop(idx)
            bot.answer_callback_query(call.id, f"🗑 {removed['brand']} {removed['model']} удалён")
            try:
                bot.delete_message(user_id, call.message.id)
            except Exception:
                pass
        return

    if not state:
        bot.send_message(user_id, "Напиши /start чтобы начать заново")
        bot.answer_callback_query(call.id)
        return

    step = state["step"]

    # 1) категория
    if call.data.startswith("category:") and step == "category":
        state["filters"]["category"] = call.data.split(":")[1]
        state["step"] = "fuel"
        m = InlineKeyboardMarkup()
        for f in FUEL_MAP:
            m.add(InlineKeyboardButton(f, callback_data=f"fuel:{f}"))
        bot.edit_message_text("Выбери тип топлива:", user_id, call.message.id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    # 2) топливо
    if call.data.startswith("fuel:") and step == "fuel":
        fuel = call.data.split(":")[1]
        state["filters"]["fuel_type"] = FUEL_MAP[fuel]
        state["step"] = "color"
        m = InlineKeyboardMarkup()
        for c in COLOR_MAP:
            m.add(InlineKeyboardButton(c, callback_data=f"color:{c}"))
        bot.edit_message_text("Выбери цвет авто:", user_id, call.message.id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    # 3) цвет
    if call.data.startswith("color:") and step == "color":
        color = call.data.split(":")[1]
        state["filters"]["color"] = COLOR_MAP[color]
        state["step"] = "condition"
        m = InlineKeyboardMarkup()
        for c in COND_MAP:
            m.add(InlineKeyboardButton(c, callback_data=f"condition:{c}"))
        bot.edit_message_text("Выбери состояние авто:", user_id, call.message.id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    # 4) состояние
    if call.data.startswith("condition:") and step == "condition":
        cond = call.data.split(":")[1]
        state["filters"]["condition"] = COND_MAP[cond]
        state["step"] = "price"
        m = InlineKeyboardMarkup()
        for p in PRICE_MAP:
            m.add(InlineKeyboardButton(p, callback_data=f"price:{p}"))
        bot.edit_message_text("Выбери диапазон цены (KGS):", user_id, call.message.id, reply_markup=m)
        bot.answer_callback_query(call.id)
        return

    # 5) цена → выдача
    if call.data.startswith("price:") and step == "price":
        price = call.data.split(":")[1]
        price_min, price_max = PRICE_MAP[price]
        state["filters"]["price_min"] = price_min
        state["filters"]["price_max"] = price_max
        state["step"] = "done"

        # Убираем клавиатуру у сообщения с ценами, чтобы «кнопки цен» исчезли
        try:
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.id, reply_markup=None)
        except Exception:
            pass

        # запрос к API
        try:
            r = requests.get(API_URL, params=state["filters"], timeout=10)
            r.raise_for_status()
            state["cars"] = r.json()
            state["index"] = 0
        except Exception as e:
            bot.send_message(user_id, f"❌ Ошибка API: {e}")
            user_state.pop(user_id, None)
            bot.answer_callback_query(call.id)
            return

        if state["cars"]:
            send_car_message(user_id)     # присылаем НОВОЕ сообщение с карточкой
        else:
            bot.send_message(user_id, "❌ Авто по твоему запросу не найдено.")
            user_state.pop(user_id, None)

        bot.answer_callback_query(call.id)
        return

    # пагинация
    if call.data in ("prev", "next") and state.get("cars"):
        if call.data == "prev" and state["index"] > 0:
            state["index"] -= 1
        elif call.data == "next" and state["index"] < len(state["cars"]) - 1:
            state["index"] += 1
        update_car_message(user_id)
        bot.answer_callback_query(call.id)
        return

    # избранное
    if call.data == "favorite" and state.get("cars"):
        car = state["cars"][state["index"]]
        favs = favorites.setdefault(user_id, [])
        if car not in favs:
            favs.append(car)
            bot.answer_callback_query(call.id, "⭐ Добавлено в избранное!")
        else:
            bot.answer_callback_query(call.id, "Уже в избранном ✅")
        return

# -------------------- run --------------------
bot.polling(none_stop=True)
