import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# ═══════════════════════════════════════
# Берём токен из переменных окружения (безопасно для Render)
TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_ОТ_@BotFather")
WEB_APP_URL = "https://bombizo.github.io/quiz"
CHANNEL_ID = "@beautycosmet1ics"
# ═══════════════════════════════════════

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    welcome_text = """👋 Добро пожаловать, {name}!

🔥 Я собираю актуальные промокоды, скидки и полезную информацию по уходу за кожей.

🌞 Калькулятор фототипа SPF:
4 вопроса + ваш SPF и UV-индекс → точное безопасное время на солнце. Промокоды на средства под ваш результат — в канале @beautycosmet1ics.

Канал: @beautycosmet1ics
Мини-приложение: https://t.me/spf_calc_bot""".format(name=update.effective_user.first_name)

    keyboard = [
        [InlineKeyboardButton(
            text="🌞 Открыть калькулятор SPF",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )],
        [InlineKeyboardButton(
            text="📢 Наш Telegram канал",
            url="https://t.me/beautycosmet1ics"
        )]
    ]

    # Пробуем отправить PNG, если нет — JPG, если нет — текст
    photo_paths = ['photo.png', 'photo.jpg', 'photo.jpeg']
    sent = False

    for path in photo_paths:
        try:
            with open(path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=welcome_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            sent = True
            break
        except FileNotFoundError:
            continue

    if not sent:
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    print("🤖 Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
