import os
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ═══════════════════════════════════════
TOKEN = os.environ.get("TOKEN", "ВСТАВЬ_ТОКЕН_ОТ_@BotFather")
WEB_APP_URL = "https://bombizo.github.io/quiz"
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_URL", "https://spf-calc-bot.onrender.com")
CHANNEL_ID = "@beautycosmet1ics"
# ═══════════════════════════════════════

# Flask app
app = Flask(__name__)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаём Application
application = Application.builder().token(TOKEN).build()


# ═══════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False


async def ask_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """🔒 Доступ к калькулятору только для подписчиков канала!

Подпишитесь на @beautycosmet1ics и возвращайтесь — бот станет доступен автоматически."""

    keyboard = [
        [InlineKeyboardButton("📢 Подписаться на канал", url="https://t.me/beautycosmet1ics")],
        [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscribe")]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ═══════════════════════════════════════════════════════════════
# ОБРАБОТЧИКИ
# ═══════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        return await ask_subscribe(update, context)

    welcome_text = """👋 Добро пожаловать, {name}!

🔥 Я собираю актуальные промокоды, скидки и полезную информацию по уходу за кожей.

🌞 Калькулятор фототипа SPF:
4 вопроса + ваш SPF и UV-индекс → точное безопасное время на солнце. Промокоды на средства под ваш результат — в канале @beautycosmet1ics.

Канал: @beautycosmet1ics
Мини-приложение: https://t.me/spf_calc_bot""".format(name=update.effective_user.first_name)

    keyboard = [
        [InlineKeyboardButton("🌞 Открыть калькулятор SPF", callback_data="open_calculator")],
        [InlineKeyboardButton("📢 Наш Telegram канал", url="https://t.me/beautycosmet1ics")]
    ]

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


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    is_subscribed = await check_subscription(user_id, context)

    if is_subscribed:
        await query.answer("✅ Подписка подтверждена!")
        await query.delete_message()
        await start(update, context)
    else:
        await query.answer("❌ Вы ещё не подписались на канал!", show_alert=True)
        await query.message.reply_text(
            "❌ Проверка не пройдена! Вы не подписаны на @beautycosmet1ics.\n\n"
            "👉 Подпишитесь на канал и нажмите кнопку «✅ Я подписался» ещё раз.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Подписаться на канал", url="https://t.me/beautycosmet1ics")],
                [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscribe")]
            ])
        )


async def open_calculator_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    is_subscribed = await check_subscription(user_id, context)

    if not is_subscribed:
        await query.answer("❌ Доступ только для подписчиков!", show_alert=True)
        await ask_subscribe(update, context)
        return

    await query.answer("🌞 Открываю калькулятор...")

    await query.message.reply_text(
        "🌞 Нажмите кнопку ниже, чтобы открыть калькулятор:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🧴 Открыть калькулятор SPF", web_app=WebAppInfo(url=WEB_APP_URL))]
        ])
    )


# Регистрируем обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler, pattern="^check_subscribe$"))
application.add_handler(CallbackQueryHandler(open_calculator_handler, pattern="^open_calculator$"))


# ═══════════════════════════════════════════════════════════════
# ИНИЦИАЛИЗАЦИЯ (без фонового потока!)
# ═══════════════════════════════════════════════════════════════

# Инициализируем application один раз при импорте
# В Render это выполняется при старте сервиса
asyncio.run(application.initialize())


# ═══════════════════════════════════════════════════════════════
# FLASK ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return '🤖 Бот работает!'


@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Получает обновления от Telegram"""
    update = Update.de_json(request.get_json(force=True), application.bot)
    
    # Создаём новый event loop для каждого запроса
    # python-telegram-bot v20+ корректно работает с новым loop
    try:
        asyncio.run(application.process_update(update))
    except Exception as e:
        logger.error(f"Ошибка обработки update: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    return jsonify({'status': 'ok'})


@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = f"{WEBHOOK_BASE_URL}/{TOKEN}"
    
    try:
        result = asyncio.run(application.bot.set_webhook(url=webhook_url))
        if result:
            return f'✅ Webhook установлен: {webhook_url}'
        else:
            return '❌ Ошибка установки webhook'
    except Exception as e:
        return f'❌ Ошибка: {e}'


@app.route('/delete_webhook', methods=['GET'])
def delete_webhook():
    try:
        result = asyncio.run(application.bot.delete_webhook())
        if result:
            return '✅ Webhook удалён'
        else:
            return '❌ Ошибка удаления webhook'
    except Exception as e:
        return f'❌ Ошибка: {e}'


if __name__ == '__main__':
    app.run(debug=True, port=5000)
