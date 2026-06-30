import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("TOKEN", "ВСТАВЬ_ТОКЕН_ОТ_@BotFather")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    app.run_polling()


if __name__ == "__main__":
    main()
