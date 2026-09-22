import asyncio
import logging
from datetime import date

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from my_land_bot.models import LandPlot, SentReminder, User
from my_land_bot.services.reminders import ReminderPlan, plans_for_auction, plans_for_notice

logger = logging.getLogger(__name__)


def source_line(url: str | None) -> str:
    return f"\nИсточник: {url}" if url else "\nИсточник не добавлен — проверьте сайт администрации или ГИС Торги."


async def send_once(session: AsyncSession, bot: Bot, plot: LandPlot, telegram_id: int, plan: ReminderPlan, source_url: str | None) -> None:
    reminder = SentReminder(plot_id=plot.id, kind=plan.kind, due_date=plan.due_date)
    session.add(reminder)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return
    label = plot.cadastral_number or plot.address or f"участок #{plot.id}"
    text = f"📌 <b>{label}</b>\n{plan.text}{source_line(source_url)}\n\nПроверьте информацию в официальном источнике."
    await bot.send_message(telegram_id, text, parse_mode="HTML", disable_web_page_preview=True)
    await session.commit()


async def run_reminders_once(factory: async_sessionmaker[AsyncSession], bot: Bot, today: date | None = None) -> None:
    check_date = today or date.today()
    async with factory() as session:
        statement = select(LandPlot).join(LandPlot.user).options(selectinload(LandPlot.notice), selectinload(LandPlot.auction), selectinload(LandPlot.user)).where(LandPlot.tracking_enabled.is_(True))
        plots = list(await session.scalars(statement))
        for plot in plots:
            plans: list[tuple[ReminderPlan, str | None]] = []
            if plot.notice:
                plans.extend((plan, plot.notice.source_url) for plan in plans_for_notice(plot.notice.deadline, check_date))
            if plot.auction:
                plans.extend((plan, plot.auction.source_url) for plan in plans_for_auction(plot.auction.application_deadline, plot.auction.auction_date, check_date))
            for plan, source in plans:
                try:
                    await send_once(session, bot, plot, plot.user.telegram_id, plan, source)
                except Exception:
                    logger.exception("Could not send reminder for plot_id=%s", plot.id)
                    await session.rollback()


async def reminder_loop(factory: async_sessionmaker[AsyncSession], bot: Bot, seconds: int) -> None:
    while True:
        await run_reminders_once(factory, bot)
        await asyncio.sleep(seconds)
