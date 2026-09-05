import os
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

# Товары магазина
PRODUCTS = [
    {
        "id": 1,
        "name": "Товар 1",
        "price": 100,
        "description": "Описание товара"
    },
    {
        "id": 2,
        "name": "Товар 2",
        "price": 200,
        "description": "Описание товара"
    }
]

users = {}
orders = {}


def main_menu():
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("🛒 Каталог", callback_data="catalog"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile")
    )

    keyboard.add(
        types.InlineKeyboardButton("🛍 Мои покупки", callback_data="purchases"),
        types.InlineKeyboardButton("📜 История заказов", callback_data="orders")
    )

    keyboard.add(
        types.InlineKeyboardButton("💳 Пополнить баланс", callback_data="balance"),
        types.InlineKeyboardButton("🎁 Промокод", callback_data="promo")
    )

    keyboard.add(
        types.InlineKeyboardButton("💬 Поддержка", callback_data="support"),
        types.InlineKeyboardButton("ℹ️ О магазине", callback_data="about")
    )

    return keyboard


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id

    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "purchases": []
        }

    bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать в магазин!\n\n"
        "Выбери нужный раздел:",
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):

    user_id = call.from_user.id

    if call.data == "catalog":
        keyboard = types.InlineKeyboardMarkup()

        for product in PRODUCTS:
            keyboard.add(
                types.InlineKeyboardButton(
                    f"{product['name']} — {product['price']} ₽",
                    callback_data=f"product_{product['id']}"
                )
            )

        keyboard.add(
            types.InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )

        bot.edit_message_text(
            "🛒 <b>Каталог</b>\n\nВыбери товар:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    elif call.data.startswith("product_"):
        product_id = int(call.data.split("_")[1])

        product = next(
            (p for p in PRODUCTS if p["id"] == product_id),
            None
        )

        if not product:
            bot.answer_callback_query(call.id, "Товар не найден")
            return

        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(
            types.InlineKeyboardButton(
                "🛒 Купить",
                callback_data=f"buy_{product_id}"
            )
        )

        keyboard.add(
            types.InlineKeyboardButton(
                "◀️ Назад",
                callback_data="catalog"
            )
        )

        text = (
            f"📦 <b>{product['name']}</b>\n\n"
            f"{product['description']}\n\n"
            f"💰 Цена: <b>{product['price']} ₽</b>"
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    elif call.data.startswith("buy_"):
        product_id = int(call.data.split("_")[1])

        product = next(
            (p for p in PRODUCTS if p["id"] == product_id),
            None
        )

        if not product:
            bot.answer_callback_query(call.id, "Товар не найден")
            return

        order_id = len(orders) + 1

        orders[order_id] = {
            "user_id": user_id,
            "product": product["name"],
            "price": product["price"],
            "status": "Ожидает оплаты"
        }

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            f"🧾 <b>Заказ №{order_id}</b>\n\n"
            f"📦 {product['name']}\n"
            f"💰 {product['price']} ₽\n\n"
            "💳 Оплата пока не подключена.\n"
            "После подключения платёжной системы здесь появится кнопка оплаты.",
            parse_mode="HTML"
        )

    elif call.data == "profile":
        user = users.get(user_id, {"balance": 0, "purchases": []})

        bot.edit_message_text(
            f"👤 <b>Профиль</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"💰 Баланс: {user['balance']} ₽\n"
            f"🛍 Покупок: {len(user['purchases'])}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    "◀️ Назад",
                    callback_data="menu"
                )
            ),
            parse_mode="HTML"
        )

    elif call.data == "purchases":
        user = users.get(user_id, {"purchases": []})

        if not user["purchases"]:
            text = "🛍 <b>Мои покупки</b>\n\nПокупок пока нет."
        else:
            text = "🛍 <b>Мои покупки</b>\n\n"

            for purchase in user["purchases"]:
                text += f"• {purchase}\n"

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    "◀️ Назад",
                    callback_data="menu"
                )
            ),
            parse_mode="HTML"
        )

    elif call.data == "orders":
        user_orders = [
            (order_id, order)
            for order_id, order in orders.items()
            if order["user_id"] == user_id
        ]

        if not user_orders:
            text = "📜 <b>История заказов</b>\n\nЗаказов пока нет."
        else:
            text = "📜 <b>История заказов</b>\n\n"

            for order_id, order in user_orders:
                text += (
                    f"№{order_id} — {order['product']} — "
                    f"{order['price']} ₽ — {order['status']}\n"
                )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    "◀️ Назад",
                    callback_data="menu"
                )
            ),
            parse_mode="HTML"
        )

    elif call.data == "balance":
        bot.edit_message_text(
            "💳 <b>Пополнение баланса</b>\n\n"
            "Платёжная система пока не подключена.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    "◀️ Назад",
                    callback_data="menu"
                )
            ),
            parse_mode="HTML"
        )

    elif call.data == "promo":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "🎁 Отправь промокод следующим сообщением."
        )

    elif call.data == "support":
        bot.edit_message_text(
            "💬 <b>Поддержка</b>\n\n"
            "Свяжись с администратором магазина.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    "◀️ Назад",
                    callback_data="menu"
                )
            ),
            parse_mode="HTML"
        )

    elif call.data == "about":
        bot.edit_message_text(
            "ℹ️ <b>О магазине</b>\n\n"
            "Добро пожаловать в наш магазин!",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    "◀️ Назад",
                    callback_data="menu"
                )
            ),
            parse_mode="HTML"
        )

    elif call.data == "menu":
        bot.edit_message_text(
            "🏠 <b>Главное меню</b>\n\nВыбери нужный раздел:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu(),
            parse_mode="HTML"
        )


print("Бот запущен!")
bot.infinity_polling()
