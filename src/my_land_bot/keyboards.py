from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить мой участок", callback_data="plot:add")],
        [InlineKeyboardButton(text="📍 Мои участки", callback_data="plot:list")],
        [InlineKeyboardButton(text="Как это работает", callback_data="help:how"), InlineKeyboardButton(text="Помощь", callback_data="help:disclaimer")],
    ])


def plot_actions(plot_id: int, tracking_enabled: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить извещение", callback_data=f"notice:add:{plot_id}")],
        [InlineKeyboardButton(text="Добавить аукцион", callback_data=f"auction:add:{plot_id}")],
        [InlineKeyboardButton(text="Отключить контроль" if tracking_enabled else "Включить контроль", callback_data=f"plot:toggle:{plot_id}")],
    ])
