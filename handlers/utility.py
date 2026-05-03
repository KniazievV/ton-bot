import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from handlers.keyboards import BTN_INFO, BTN_RESTART, BTN_TON_RATE, main_menu_kb

log = logging.getLogger(__name__)
from handlers.start import send_main_screen
from ton_price import fetch_ton_usdt_market, format_ton_rate_message

router = Router(name="utility")


@router.message(F.text == BTN_RESTART)
async def restart_button(message: Message, state: FSMContext) -> None:
    await state.clear()
    await send_main_screen(message)


@router.message(F.text == BTN_TON_RATE)
async def ton_rate_button(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        m = await fetch_ton_usdt_market()
        text = format_ton_rate_message(m)
    except Exception:
        log.exception("CoinGecko TON rate failed")
        text = "Не удалось получить курс (CoinGecko недоступен или лимит запросов). Попробуйте через минуту"
    await message.answer(text, reply_markup=main_menu_kb())


@router.message(F.text == BTN_INFO)
async def info_button(message: Message) -> None:
    await message.answer(
        "Шо ты, голова, нет тут ничего интересного. Иди воркай 😘",
        reply_markup=main_menu_kb(),
    )
