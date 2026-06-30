import os
import threading
import asyncio
import sys

from flask import Flask

# Добавляем текущую директорию в путь, чтобы импортировать bot.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import main

app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    """Запускает Telegram-бота (polling) в фоновом потоке."""
    asyncio.run(main())

# Запускаем бота в отдельном потоке, чтобы Flask мог слушать порт для Render
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
