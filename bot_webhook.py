import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler

TOKEN = os.environ.get("TOKEN", "ВСТАВЬ_ТОКЕН")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://spf-calc-bot.onrender.com")
PORT = int(os.environ.get("PORT", 10000))


async def start(update, context):
    text = f"👋 Привет, {update.effective_user.first_name}!\n\n🌞 Калькулятор фототипа SPF — узнай точное безопасное время на солнце.\n\nКанал: @beautycosmet1ics"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/beautycosmet1ics")]
    ])

    for path in ("photo.png", "photo.jpg", "photo.jpeg"):
        if os.path.exists(path):
            with open(path, "rb") as f:
                await update.message.reply_photo(photo=f, caption=text, reply_markup=keyboard)
            return

    await update.message.reply_text(text, reply_markup=keyboard)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
    )


if __name__ == "__main__":
    main()
