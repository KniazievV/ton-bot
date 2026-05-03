from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_ADD = "➕ Добавить"
BTN_LIST = "📋 Список"
BTN_DELETE = "🗑 Удалить"
BTN_RESTART = "Рестарт"
BTN_TON_RATE = "Курс TON"
BTN_INFO = "Инфо"


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_ADD),
                KeyboardButton(text=BTN_LIST),
                KeyboardButton(text=BTN_DELETE),
            ],
            [
                KeyboardButton(text=BTN_RESTART),
                KeyboardButton(text=BTN_TON_RATE),
                KeyboardButton(text=BTN_INFO),
            ],
        ],
        resize_keyboard=True,
        persistent=True,
    )
