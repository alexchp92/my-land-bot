from datetime import date

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from my_land_bot.keyboards import menu, plot_actions
from my_land_bot.models import Auction, LandPlot, Notice, PlotStatus, User


class AddPlot(StatesGroup):
    cadastral = State()
    region = State()
    municipality = State()
    submitted = State()
    authority = State()
    address = State()
    comment = State()


class AddNotice(StatesGroup):
    source = State()
    deadline = State()


class AddAuction(StatesGroup):
    source = State()
    application_deadline = State()
    auction_date = State()


DISCLAIMER = "\n\n⚠️ Бот — информационный помощник, а не юридическое заключение. Он не гарантирует предоставление участка. Проверяйте сведения и документы в официальном источнике."


async def user_for(session: AsyncSession, telegram_id: int) -> User:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.flush()
    return user


async def plot_for(session: AsyncSession, plot_id: int, telegram_id: int) -> LandPlot | None:
    query = select(LandPlot).join(LandPlot.user).options(selectinload(LandPlot.notice), selectinload(LandPlot.auction)).where(LandPlot.id == plot_id, User.telegram_id == telegram_id)
    return await session.scalar(query)


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def plot_label(plot: LandPlot) -> str:
    return plot.cadastral_number or plot.address or f"Участок #{plot.id}"


def status_text(status: PlotStatus) -> str:
    return {PlotStatus.WAITING_NOTICE: "Ждём извещение", PlotStatus.THIRD_PARTY_WINDOW: "Идёт срок для заявлений третьих лиц", PlotStatus.AUCTION_TRACKED: "Аукцион отслеживается", PlotStatus.COMPLETED: "Завершено"}[status]


def build_router(factory: async_sessionmaker[AsyncSession]) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        async with factory() as session:
            await user_for(session, message.from_user.id)
            await session.commit()
        await message.answer("Здравствуйте! Я помогу сохранить данные по вашему участку после подачи заявления, не пропустить срок по извещению и возможный аукцион." + DISCLAIMER, reply_markup=menu())

    @router.callback_query(F.data == "help:how")
    async def how(callback: CallbackQuery) -> None:
        await callback.message.answer("1. Добавьте участок и дату подачи заявления.\n2. Когда найдёте извещение, сохраните ссылку и срок.\n3. Если появится аукцион — добавьте его данные.\n4. Бот напомнит о контрольных датах.\n\nЕсли других заявлений нет и отсутствуют основания для отказа, участок может быть предоставлен без торгов. Если появятся другие заинтересованные лица, участок могут выставить на аукцион." + DISCLAIMER)
        await callback.answer()

    @router.callback_query(F.data == "help:disclaimer")
    async def disclaimer(callback: CallbackQuery) -> None:
        await callback.message.answer(DISCLAIMER.strip())
        await callback.answer()

    @router.callback_query(F.data == "plot:add")
    async def add_plot(callback: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(AddPlot.cadastral)
        await callback.message.answer("Введите кадастровый номер участка. Если его нет, отправьте «-» — точность отслеживания может быть ниже.")
        await callback.answer()

    @router.message(AddPlot.cadastral)
    async def add_cadastral(message: Message, state: FSMContext) -> None:
        await state.update_data(cadastral_number=None if message.text.strip() == "-" else message.text.strip())
        await state.set_state(AddPlot.region)
        await message.answer("Укажите регион.")

    @router.message(AddPlot.region)
    async def add_region(message: Message, state: FSMContext) -> None:
        await state.update_data(region=message.text.strip())
        await state.set_state(AddPlot.municipality)
        await message.answer("Укажите муниципалитет.")

    @router.message(AddPlot.municipality)
    async def add_municipality(message: Message, state: FSMContext) -> None:
        await state.update_data(municipality=message.text.strip())
        await state.set_state(AddPlot.submitted)
        await message.answer("Дата подачи заявления в формате ГГГГ-ММ-ДД.")

    @router.message(AddPlot.submitted)
    async def add_submitted(message: Message, state: FSMContext) -> None:
        submitted = parse_date(message.text)
        if not submitted or submitted > date.today():
            await message.answer("Нужна корректная дата не из будущего, например 2026-09-22.")
            return
        await state.update_data(submitted_at=submitted)
        await state.set_state(AddPlot.authority)
        await message.answer("Укажите администрацию или орган. Если не знаете, отправьте «-».")

    @router.message(AddPlot.authority)
    async def add_authority(message: Message, state: FSMContext) -> None:
        await state.update_data(authority=None if message.text.strip() == "-" else message.text.strip())
        await state.set_state(AddPlot.address)
        await message.answer("Укажите адрес или ориентир. Если не знаете, отправьте «-».")

    @router.message(AddPlot.address)
    async def add_address(message: Message, state: FSMContext) -> None:
        await state.update_data(address=None if message.text.strip() == "-" else message.text.strip())
        await state.set_state(AddPlot.comment)
        await message.answer("Добавьте комментарий или отправьте «-». После этого участок будет сохранён.")

    @router.message(AddPlot.comment)
    async def add_comment(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        async with factory() as session:
            user = await user_for(session, message.from_user.id)
            plot = LandPlot(user_id=user.id, comment=None if message.text.strip() == "-" else message.text.strip(), **data)
            session.add(plot)
            await session.commit()
        await state.clear()
        await message.answer(f"Участок «{plot_label(plot)}» сохранён. Статус: Ждём извещение.", reply_markup=plot_actions(plot.id, True))

    @router.callback_query(F.data == "plot:list")
    async def list_plots(callback: CallbackQuery) -> None:
        async with factory() as session:
            user = await user_for(session, callback.from_user.id)
            plots = list(await session.scalars(select(LandPlot).where(LandPlot.user_id == user.id).order_by(LandPlot.created_at.desc())))
            await session.commit()
        if not plots:
            await callback.message.answer("У вас пока нет участков. Добавьте первый — и я начну вести его карточку.", reply_markup=menu())
        else:
            for plot in plots:
                await callback.message.answer(f"📍 <b>{plot_label(plot)}</b>\n{plot.region} · {plot.municipality}\nСтатус: <b>{status_text(plot.status)}</b>", parse_mode="HTML", reply_markup=plot_actions(plot.id, plot.tracking_enabled))
        await callback.answer()

    @router.callback_query(F.data.startswith("plot:toggle:"))
    async def toggle(callback: CallbackQuery) -> None:
        plot_id = int(callback.data.rsplit(":", 1)[1])
        async with factory() as session:
            plot = await plot_for(session, plot_id, callback.from_user.id)
            if not plot:
                await callback.answer("Участок не найден", show_alert=True)
                return
            plot.tracking_enabled = not plot.tracking_enabled
            await session.commit()
            enabled = plot.tracking_enabled
        await callback.message.answer("Контроль включён." if enabled else "Контроль отключён. Напоминания не будут приходить.")
        await callback.answer()

    @router.callback_query(F.data.startswith("notice:add:"))
    async def add_notice(callback: CallbackQuery, state: FSMContext) -> None:
        await state.update_data(plot_id=int(callback.data.rsplit(":", 1)[1]))
        await state.set_state(AddNotice.source)
        await callback.message.answer("Отправьте ссылку на официальное извещение или «-», если ссылки пока нет.")
        await callback.answer()

    @router.message(AddNotice.source)
    async def notice_source(message: Message, state: FSMContext) -> None:
        await state.update_data(source_url=None if message.text.strip() == "-" else message.text.strip())
        await state.set_state(AddNotice.deadline)
        await message.answer("Укажите дату окончания приёма заявлений: ГГГГ-ММ-ДД.")

    @router.message(AddNotice.deadline)
    async def notice_deadline(message: Message, state: FSMContext) -> None:
        deadline = parse_date(message.text)
        if not deadline:
            await message.answer("Нужна дата в формате ГГГГ-ММ-ДД.")
            return
        data = await state.get_data()
        async with factory() as session:
            plot = await plot_for(session, data["plot_id"], message.from_user.id)
            if not plot:
                await message.answer("Участок не найден.")
                await state.clear()
                return
            plot.notice = Notice(source_url=data["source_url"], deadline=deadline)
            plot.status = PlotStatus.THIRD_PARTY_WINDOW
            await session.commit()
        await state.clear()
        await message.answer("Извещение сохранено. Напоминания включены за 7, 3 и 1 день, в день окончания срока и через 2 дня после него." + DISCLAIMER)

    @router.callback_query(F.data.startswith("auction:add:"))
    async def add_auction(callback: CallbackQuery, state: FSMContext) -> None:
        await state.update_data(plot_id=int(callback.data.rsplit(":", 1)[1]))
        await state.set_state(AddAuction.source)
        await callback.message.answer("Отправьте ссылку на официальный аукцион или «-».")
        await callback.answer()

    @router.message(AddAuction.source)
    async def auction_source(message: Message, state: FSMContext) -> None:
        await state.update_data(source_url=None if message.text.strip() == "-" else message.text.strip())
        await state.set_state(AddAuction.application_deadline)
        await message.answer("Укажите окончание подачи заявки (ГГГГ-ММ-ДД) или «-».")

    @router.message(AddAuction.application_deadline)
    async def auction_deadline(message: Message, state: FSMContext) -> None:
        value = None if message.text.strip() == "-" else parse_date(message.text)
        if message.text.strip() != "-" and not value:
            await message.answer("Нужна дата в формате ГГГГ-ММ-ДД или «-».")
            return
        await state.update_data(application_deadline=value)
        await state.set_state(AddAuction.auction_date)
        await message.answer("Укажите дату аукциона (ГГГГ-ММ-ДД) или «-».")

    @router.message(AddAuction.auction_date)
    async def auction_date(message: Message, state: FSMContext) -> None:
        value = None if message.text.strip() == "-" else parse_date(message.text)
        if message.text.strip() != "-" and not value:
            await message.answer("Нужна дата в формате ГГГГ-ММ-ДД или «-».")
            return
        data = await state.get_data()
        async with factory() as session:
            plot = await plot_for(session, data["plot_id"], message.from_user.id)
            if not plot:
                await message.answer("Участок не найден.")
                return
            plot.auction = Auction(source_url=data["source_url"], application_deadline=data["application_deadline"], auction_date=value)
            plot.status = PlotStatus.AUCTION_TRACKED
            await session.commit()
        await state.clear()
        await message.answer("Аукцион сохранён. Напоминания по срокам включены." + DISCLAIMER)

    return router
