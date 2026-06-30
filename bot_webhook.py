import os
import logging
import asyncio
import threading
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ═══════════════════════════════════════
TOKEN = os.environ.get("TOKEN", "ВСТАВЬ_ТОКЕН_ОТ_@BotFather")
WEB_APP_URL = "https://bombizo.github.io/quiz"
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_URL", "https://spf-calc-bot.onrender.com")
CHANNEL_ID = "@beautycosmet1ics"
# ═══════════════════════════════════════

app = Flask(__name__)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальные переменные (заполняются в фоновом потоке)
application = None
bot_loop = None
ready_event = threading.Event()


# ═══════════════════════════════════════════════════════════════
# ОБРАБОТЧИКИ
# ═══════════════════════════════════════════════════════════════

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}", exc_info=True)
        return False


async def ask_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """🔒 Доступ к калькулятору только для подписчиков канала!

Подпишитесь на @beautycosmet1ics и возвращайтесь — бот станет доступен автоматически."""

    keyboard = [
        [InlineKeyboardButton("📢 Подписаться на канал", url="https://t.me/beautycosmet1ics")],
        [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscribe")]
    ]

    # effective_message работает и для обычных сообщений, и для callback query
    await update.effective_message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


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
    message = update.effective_message

    for path in photo_paths:
        if os.path.exists(path):
            try:
                with open(path, 'rb') as photo:
                    await message.reply_photo(
                        photo=photo,
                        caption=welcome_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                sent = True
                break
            except Exception as e:
                logger.warning(f"Не удалось отправить фото {path}: {e}")

    if not sent:
        await message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    is_subscribed = await check_subscription(user_id, context)

    if is_subscribed:
        await query.answer("✅ Подписка подтверждена!")
        try:
            await query.delete_message()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")

        # Отправляем приветствие новым сообщением, а не через start(),
        # иначе reply на удалённое сообщение упадёт
        welcome_text = """👋 Добро пожаловать, {name}!

🔥 Я собираю актуальные промокоды, скидки и полезную информацию по уходу за кожей.

🌞 Калькулятор фототипа SPF:
4 вопроса + ваш SPF и UV-индекс → точное безопасное время на солнце. Промокоды на средства под ваш результат — в канале @beautycosmet1ics.

Канал: @beautycosmet1ics
Мини-приложение: https://t.me/spf_calc_bot""".format(name=query.from_user.first_name)

        keyboard = [
            [InlineKeyboardButton("🌞 Открыть калькулятор SPF", callback_data="open_calculator")],
            [InlineKeyboardButton("📢 Наш Telegram канал", url="https://t.me/beautycosmet1ics")]
        ]

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
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


def setup_handlers(app_instance):
    app_instance.add_handler(CommandHandler("start", start))
    app_instance.add_handler(CallbackQueryHandler(button_handler, pattern="^check_subscribe$"))
    app_instance.add_handler(CallbackQueryHandler(open_calculator_handler, pattern="^open_calculator$"))


# ═══════════════════════════════════════════════════════════════
# ФОНОВЫЙ ПОТОК: Создаём Application внутри loop
# ═══════════════════════════════════════════════════════════════

def run_bot():
    global application, bot_loop
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)

    application = Application.builder().token(TOKEN).build()
    setup_handlers(application)

    # Инициализация + запуск внутренних механизмов PTB
    bot_loop.run_until_complete(application.initialize())
    bot_loop.run_until_complete(application.start())
    logger.info("✅ Application initialized and started")

    # Сигнализируем Flask, что можно принимать запросы
    ready_event.set()

    # Держим loop открытым для обработки webhook-запросов
    bot_loop.run_forever()


# Запускаем бота в фоновом потоке
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

# Ждём инициализации (макс 15 сек)
if not ready_event.wait(timeout=15):
    logger.error("❌ Таймаут инициализации бота!")

logger.info(f"🚀 Bot ready: alive={bot_thread.is_alive()}, app={application is not None}")


# ═══════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: Запуск async в фоновом loop
# ═══════════════════════════════════════════════════════════════

def run_async(coro, timeout=30):
    """Выполняет корутину в bot_loop и возвращает результат"""
    if bot_loop is None or application is None:
        raise RuntimeError("Bot not initialized")
    future = asyncio.run_coroutine_threadsafe(coro, bot_loop)
    return future.result(timeout=timeout)


# ═══════════════════════════════════════════════════════════════
# FLASK ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return '🤖 Бот работает!'


@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    # Защита от запросов до готовности бота
    if application is None or bot_loop is None:
        logger.warning("⏳ Бот ещё не инициализирован, возвращаем 503")
        return jsonify({'status': 'not_ready'}), 503

    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        # ⭐ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: не блокируем Flask.
        # Ставим задачу в очередь фонового loop и сразу отвечаем Telegram 200 OK.
        asyncio.run_coroutine_threadsafe(application.process_update(update), bot_loop)
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Ошибка обработки update: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    if application is None or bot_loop is None:
        return '❌ Бот ещё не готов', 503

    try:
        webhook_url = f"{WEBHOOK_BASE_URL}/{TOKEN}"
        result = run_async(application.bot.set_webhook(url=webhook_url), timeout=30)
        if result:
            return f'✅ Webhook установлен: {webhook_url}'
        else:
            return '❌ Ошибка установки webhook'
    except Exception as e:
        logger.error(f"Ошибка set_webhook: {e}", exc_info=True)
        return f'❌ Ошибка: {str(e)}'


@app.route('/delete_webhook', methods=['GET'])
def delete_webhook():
    if application is None or bot_loop is None:
        return '❌ Бот ещё не готов', 503

    try:
        result = run_async(application.bot.delete_webhook(), timeout=30)
        if result:
            return '✅ Webhook удалён'
        else:
            return '❌ Ошибка удаления webhook'
    except Exception as e:
        return f'❌ Ошибка: {e}'


if __name__ == '__main__':
    app.run(debug=True, port=5000)
