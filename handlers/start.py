from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from handlers.keyboards import main_menu_kb

router = Router(name="start")

MAIN_SCREEN_TEXT = (
    "Приветствую ✌️\n"
    "Я слежу за балансом кошельков в сети TON и TRON и пришлю уведомление, "
    "если баланс пополнится"
)


async def send_main_screen(message: Message) -> None:
    await message.answer(MAIN_SCREEN_TEXT, reply_markup=main_menu_kb())


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await send_main_screen(message)
