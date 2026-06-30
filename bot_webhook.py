import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ═══════════════════════════════════════
TOKEN = os.environ.get("TOKEN", "ВСТАВЬ_ТОКЕН_ОТ_@BotFather")
WEB_APP_URL = "https://bombizo.github.io/quiz"
CHANNEL_ID = "@beautycosmet1ics"
# ═══════════════════════════════════════

# Flask app
app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаём Application (без запуска polling)
application = Application.builder().token(TOKEN).build()

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, подписан ли пользователь на канал"""
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Проверка подписки
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
        [InlineKeyboardButton(
            text="🌞 Открыть калькулятор SPF",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )],
        [InlineKeyboardButton(
            text="📢 Наш Telegram канал",
            url="https://t.me/beautycosmet1ics"
        )]
    ]

    # Отправляем картинку + текст с кнопками
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

async def ask_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает сообщение с требованием подписки"""
    text = """🔒 Доступ к калькулятору только для подписчиков канала!

Подпишитесь на @beautycosmet1ics и возвращайтесь — бот станет доступен автоматически."""

    keyboard = [
        [InlineKeyboardButton(
            text="📢 Подписаться на канал",
            url="https://t.me/beautycosmet1ics"
        )],
        [InlineKeyboardButton(
            text="✅ Я подписался",
            callback_data="check_subscribe"
        )]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия 'Я подписался'"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    is_subscribed = await check_subscription(user_id, context)

    if is_subscribed:
        await query.delete_message()
        await start(update, context)
    else:
        await query.answer("❌ Вы ещё не подписались на канал! Сначала подпишитесь.", show_alert=True)

# Регистрируем обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler, pattern="^check_subscribe$"))

# Flask routes
@app.route('/')
def index():
    return '🤖 Бот работает!'

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Получает обновления от Telegram"""
    update = Update.de_json(request.get_json(force=True), application.bot)

    # Обрабатываем обновление
    application.update_queue.put_nowait(update)

    return jsonify({'status': 'ok'})

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Устанавливает webhook (вызвать один раз)"""
    # Для PythonAnywhere: https://username.pythonanywhere.com/TOKEN
    webhook_url = request.host_url.rstrip('/') + f'/{TOKEN}'

    result = application.bot.set_webhook(url=webhook_url)

    if result:
        return f'✅ Webhook установлен: {webhook_url}'
    else:
        return '❌ Ошибка установки webhook'

@app.route('/delete_webhook', methods=['GET'])
def delete_webhook():
    """Удаляет webhook"""
    result = application.bot.delete_webhook()

    if result:
        return '✅ Webhook удалён'
    else:
        return '❌ Ошибка удаления webhook'

# Запускаем application (инициализация)
import asyncio
asyncio.run(application.initialize())

if __name__ == '__main__':
    # Для локального тестирования
    app.run(debug=True, port=5000)
