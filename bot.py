import asyncio

from aiogram import Bot, Dispatcher
from config import TOKEN, logger
from database import Database
from handlers import setup_handlers
from middleware import LoggingMiddleware

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.message.middleware(LoggingMiddleware())
setup_handlers(dp)


async def on_startup():
    # Инициализируем подключение к базе данных и создаём таблицы
    await Database.get_instance()
    logger.info("База данных инициализирована.")


async def main():
    await on_startup()
    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
