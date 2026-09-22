import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from my_land_bot.config import Settings
from my_land_bot.db import session_factory
from my_land_bot.handlers import build_router
from my_land_bot.services.scheduler import reminder_loop


async def main() -> None:
    settings = Settings()
    Path("data").mkdir(exist_ok=True)
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dispatcher = Dispatcher()
    factory = session_factory(settings.database_url)
    dispatcher.include_router(build_router(factory))
    scheduler = asyncio.create_task(reminder_loop(factory, bot, settings.reminder_poll_seconds))
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        await dispatcher.start_polling(bot)
    finally:
        scheduler.cancel()
        await bot.session.close()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
