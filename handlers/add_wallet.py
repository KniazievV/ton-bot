import html
import sqlite3

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import db
from handlers.keyboards import BTN_ADD, BTN_DELETE, BTN_LIST, main_menu_kb
from handlers.messaging import HIDE_LINK_PREVIEW
from handlers.states import AddWalletStates
from ton_client import fetch_balance_nano, nano_to_ton_2dec
from tron_client import atomic_to_usdt_2dec, fetch_usdt_trc20_balance_atomic
from wallet_links import address_link_html_by_chain

router = Router(name="add_wallet")


def _chain_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="TON", callback_data="chain:TON"),
                InlineKeyboardButton(text="TRON (USDT TRC-20)", callback_data="chain:TRON"),
            ]
        ]
    )


def _notify_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="notify:1"),
                InlineKeyboardButton(text="Нет", callback_data="notify:0"),
            ]
        ]
    )


@router.message(F.text == BTN_ADD)
async def add_clicked(message: Message, state: FSMContext) -> None:
    await state.set_state(AddWalletStates.wait_chain)
    await message.answer("Выберите сеть:", reply_markup=_chain_kb())


@router.callback_query(AddWalletStates.wait_chain, F.data.startswith("chain:"))
async def chain_chosen(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    chain = (query.data.split(":", 1)[1] if query.data else "TON").strip().upper()
    if chain not in {"TON", "TRON"}:
        chain = "TON"
    await state.update_data(chain=chain)
    await state.set_state(AddWalletStates.wait_address)
    await query.message.edit_reply_markup(reply_markup=None)
    if chain == "TRON":
        await query.message.answer(
            "Отправьте адрес кошелька TRON (начинается с T). Буду отслеживать USDT (TRC-20).",
            reply_markup=main_menu_kb(),
        )
    else:
        await query.message.answer(
            "Отправьте адрес кошелька TON (формат EQ / UQ)",
            reply_markup=main_menu_kb(),
        )


@router.message(AddWalletStates.wait_address, F.text == BTN_LIST)
async def address_then_list(message: Message, state: FSMContext) -> None:
    await state.clear()
    from handlers.list_wallets import send_list  # local import to avoid cycle

    await send_list(message)


@router.message(AddWalletStates.wait_address, F.text == BTN_DELETE)
async def address_then_delete(message: Message, state: FSMContext) -> None:
    await state.clear()
    from handlers.list_wallets import send_delete_picker

    await send_delete_picker(message)


@router.message(AddWalletStates.wait_address, F.text == BTN_ADD)
async def address_then_add_again(message: Message) -> None:
    await message.answer("Сначала пришлите адрес кошелька текстом")


@router.message(AddWalletStates.wait_address)
async def address_received(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Нужен текстовый адрес")
        return
    addr = message.text.strip()
    data0 = await state.get_data()
    chain = (data0.get("chain") or "TON").strip().upper()
    try:
        if chain == "TRON":
            bal = await fetch_usdt_trc20_balance_atomic(addr)
        else:
            bal = await fetch_balance_nano(addr)
    except Exception:
        await message.answer(
            "Не удалось прочитать адрес через API\nПроверьте адрес и попробуйте снова"
        )
        return
    if await db.wallet_exists_for_user(message.from_user.id, chain, addr):
        await message.answer(
            "Этот адрес уже есть в вашем списке. Выберите другой или удалите существующий в разделе «Список»"
        )
        return
    await state.update_data(address=addr, initial_balance_nano=bal)
    await state.set_state(AddWalletStates.wait_name)
    if chain == "TRON":
        bal_s = atomic_to_usdt_2dec(str(bal))
        unit = "USDT"
    else:
        bal_s = nano_to_ton_2dec(str(bal))
        unit = "TON"
    await message.answer(
        f"Текущий баланс: <b>{bal_s}</b> {unit}\n\nКак назвать этот кошелёк?",
    )


@router.message(AddWalletStates.wait_name, F.text == BTN_DELETE)
async def name_then_delete(message: Message, state: FSMContext) -> None:
    await state.clear()
    from handlers.list_wallets import send_delete_picker

    await send_delete_picker(message)


@router.message(AddWalletStates.wait_chain, F.text.in_({BTN_LIST, BTN_DELETE}))
async def chain_then_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    if message.text == BTN_LIST:
        from handlers.list_wallets import send_list  # local import

        await send_list(message)
    else:
        from handlers.list_wallets import send_delete_picker

        await send_delete_picker(message)


@router.message(AddWalletStates.wait_name, F.text.in_({BTN_ADD, BTN_LIST}))
async def name_blocked_by_menu(message: Message) -> None:
    await message.answer("Сначала пришлите название одним сообщением (или /cancel)")


@router.message(AddWalletStates.wait_notify, F.text == BTN_DELETE)
async def notify_then_delete(message: Message, state: FSMContext) -> None:
    await state.clear()
    from handlers.list_wallets import send_delete_picker

    await send_delete_picker(message)


@router.message(AddWalletStates.wait_name)
async def name_received(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) > 120:
        await message.answer("Название должно быть текстом, не длиннее 120 символов")
        return
    await state.update_data(display_name=message.text.strip())
    await state.set_state(AddWalletStates.wait_notify)
    await message.answer(
        "Уведомлять о пополнениях?",
        reply_markup=_notify_kb(),
    )


@router.callback_query(AddWalletStates.wait_notify, F.data.startswith("notify:"))
async def notify_chosen(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    notify = query.data.split(":", 1)[1] == "1"
    data = await state.get_data()
    chain = (data.get("chain") or "TON").strip().upper()
    address = data.get("address")
    name = data.get("display_name")
    bal = data.get("initial_balance_nano")
    if not address or not name or bal is None:
        await query.message.answer("Сессия сброшена. Нажмите «Добавить» снова")
        await state.clear()
        return
    user_id = query.from_user.id
    try:
        await db.add_wallet(user_id, chain, address, name, notify, str(bal))
    except sqlite3.IntegrityError:
        await query.message.answer(
            "Этот адрес уже есть в вашем списке",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        await query.message.edit_reply_markup(reply_markup=None)
        return
    except Exception:
        await query.message.answer(
            "Не удалось сохранить кошелёк. Попробуйте ещё раз",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        await query.message.edit_reply_markup(reply_markup=None)
        return
    await state.clear()
    await query.message.edit_reply_markup(reply_markup=None)
    if chain == "TRON":
        bal_s = atomic_to_usdt_2dec(str(bal))
        unit = "USDT"
    else:
        bal_s = nano_to_ton_2dec(str(bal))
        unit = "TON"
    await query.message.answer(
        f"Готово. Кошелёк <b>{html.escape(name)}</b> сохранён\n"
        f"Сеть: <b>{chain}</b>\n"
        f"Адрес: {address_link_html_by_chain(chain, address)}\n"
        f"Уведомления: <b>{'вкл' if notify else 'выкл'}</b>\n"
        f"Баланс: <b>{bal_s}</b> {unit}",
        reply_markup=main_menu_kb(),
        link_preview_options=HIDE_LINK_PREVIEW,
    )
