import os
import asyncio
import threading
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

TOKEN = os.environ.get("TOKEN", "ВСТАВЬ_ТОКЕН")
WEB_APP_URL = "https://bombizo.github.io/quiz"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://ваш-сервис.onrender.com")

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()
bot_loop = None


async def start(update, context):
    text = f"👋 Привет, {update.effective_user.first_name}!\n\n🌞 Калькулятор фототипа SPF — узнай точное безопасное время на солнце.\n\nКанал: @beautycosmet1ics"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌞 Открыть калькулятор", callback_data="open_calculator")],
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/beautycosmet1ics")]
    ])
    for path in ("photo.png", "photo.jpg", "photo.jpeg"):
        if os.path.exists(path):
            with open(path, "rb") as f:
                await update.message.reply_photo(photo=f, caption=text, reply_markup=keyboard)
            return
    await update.message.reply_text(text, reply_markup=keyboard)


async def open_calculator(update, context):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "🌞 Нажми кнопку ниже:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🧴 Открыть калькулятор SPF", web_app=WebAppInfo(url=WEB_APP_URL))]
        ])
    )


application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(open_calculator, pattern="^open_calculator$"))


def run_bot():
    global bot_loop
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    bot_loop.run_until_complete(application.initialize())
    bot_loop.run_until_complete(application.start())
    bot_loop.run_forever()


threading.Thread(target=run_bot, daemon=True).start()


@app.route("/")
def index():
    return "🤖 Бот работает!"


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run_coroutine_threadsafe(application.process_update(update), bot_loop)
    return jsonify({"status": "ok"})


@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    url = f"{WEBHOOK_URL}/{TOKEN}"
    fut = asyncio.run_coroutine_threadsafe(application.bot.set_webhook(url=url), bot_loop)
    return f"✅ Webhook установлен: {url}" if fut.result(timeout=15) else "❌ Ошибка"


@app.route("/delete_webhook", methods=["GET"])
def delete_webhook():
    fut = asyncio.run_coroutine_threadsafe(application.bot.delete_webhook(), bot_loop)
    return "✅ Webhook удалён" if fut.result(timeout=15) else "❌ Ошибка"


if __name__ == "__main__":
    app.run(debug=True, port=5000)
