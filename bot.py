from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
import os

# === Конфигурация ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # токен из переменных окружения Render
CHANNEL = "@ваш_канал"              # ← замените на ваш канал
MINI_APP_URL = "https://t.me/ваш_бот?profile"  # ← замените на ссылку мини-приложения

# === Инициализация ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# === Текст приветствия ===
WELCOME_TEXT = (
    "👋 Добро пожаловать, {first_name}!\n\n"
    "☀️ Наш калькулятор SPF подбирает оптимальный уровень солнцезащиты "
    "под ваш тип кожи, планируемую активность и погодные условия.\n\n"
    "Канал: {channel}\n"
    "Мини-приложение: {mini_app}"
)

# === Клавиатура ===
def get_welcome_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧡 Наш Telegram канал", url=f"https://t.me/{CHANNEL.lstrip('@')}")],
        [InlineKeyboardButton(text="✅ Открыть мини-приложение", url=MINI_APP_URL)]
    ])

# === Хендлер /start ===
@router.message(Command("start"))
async def cmd_start(message: Message):
    # Путь к фото (в корне проекта на Render)
    photo_path = os.path.join(os.path.dirname(__file__), "photo.png")
    
    # Проверяем, есть ли фото локально
    if os.path.exists(photo_path):
        photo = FSInputFile(photo_path)
        await message.answer_photo(
            photo=photo,
            caption=WELCOME_TEXT.format(
                first_name=message.from_user.first_name,
                channel=CHANNEL,
                mini_app=MINI_APP_URL
            ),
            reply_markup=get_welcome_keyboard()
        )
    else:
        # Если фото нет — отправляем текст
        await message.answer(
            WELCOME_TEXT.format(
                first_name=message.from_user.first_name,
                channel=CHANNEL,
                mini_app=MINI_APP_URL
            ),
            reply_markup=get_welcome_keyboard()
        )

# === Регистрация роутера и запуск ===
dp.include_router(router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
