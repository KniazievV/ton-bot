import html

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import db
from handlers.keyboards import BTN_DELETE, BTN_LIST, main_menu_kb
from handlers.messaging import HIDE_LINK_PREVIEW
from ton_client import nano_to_ton_2dec
from tron_client import atomic_to_usdt_2dec

router = Router(name="list_wallets")


def _delete_kb(rows: list[dict]) -> InlineKeyboardMarkup:
    inkbd: list[list[InlineKeyboardButton]] = []
    for r in rows:
        raw = r["display_name"]
        label = raw if len(raw) <= 28 else raw[:27] + "…"
        inkbd.append(
            [InlineKeyboardButton(text=f"🗑 {label}", callback_data=f"delw:{r['id']}")]
        )
    inkbd.append(
        [InlineKeyboardButton(text="💥 Удалить все кошельки", callback_data="del_all_wallets")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inkbd)


async def build_list_text(user_id: int) -> str:
    rows = await db.list_wallets(user_id)
    if not rows:
        return "Пока нет ни одного кошелька. Нажмите «Добавить»"
    lines: list[str] = []
    for r in rows:
        chain = (r.get("chain") or "TON").strip().upper()
        if chain == "TRON":
            bal = atomic_to_usdt_2dec(str(r["last_balance_nano"]))
            unit = "USDT"
        else:
            bal = nano_to_ton_2dec(str(r["last_balance_nano"]))
            unit = "TON"
        addr_esc = html.escape(r["address"])
        lines.append(
            f"• <b>{html.escape(r['display_name'])}</b> — <code>{addr_esc}</code> — <b>{bal}</b> {unit}"
        )
    return "Ваши кошельки:\n\n" + "\n".join(lines)


async def send_list(message: Message) -> None:
    text = await build_list_text(message.from_user.id)
    await message.answer(
        text,
        reply_markup=main_menu_kb(),
        link_preview_options=HIDE_LINK_PREVIEW,
    )


async def send_delete_picker(message: Message) -> None:
    rows = await db.list_wallets(message.from_user.id)
    if not rows:
        await message.answer("Нечего удалять", reply_markup=main_menu_kb())
        return
    await message.answer(
        "Выберите кошелёк для удаления:",
        reply_markup=_delete_kb(rows),
    )


@router.message(F.text == BTN_LIST)
async def list_clicked(message: Message) -> None:
    await send_list(message)


@router.message(F.text == BTN_DELETE)
async def delete_menu_clicked(message: Message) -> None:
    await send_delete_picker(message)


@router.callback_query(F.data == "del_all_wallets")
async def delete_all_wallets_cb(query: CallbackQuery) -> None:
    uid = query.from_user.id
    n = await db.delete_all_wallets_for_user(uid)
    await query.answer("Готово" if n else "Уже пусто")
    msg = (
        "Все ваши кошельки удалены из списка"
        if n
        else "Кошельков в списке уже не было"
    )
    try:
        await query.message.edit_text(msg, reply_markup=None)
    except Exception:
        await query.message.answer(msg, reply_markup=main_menu_kb())


@router.callback_query(F.data.startswith("delw:"))
async def delete_wallet_cb(query: CallbackQuery) -> None:
    part = query.data.split(":", 1)[1] if query.data else ""
    try:
        wallet_id = int(part)
    except ValueError:
        await query.answer("Некорректные данные", show_alert=True)
        return
    uid = query.from_user.id
    ok = await db.delete_wallet(uid, wallet_id)
    if not ok:
        await query.answer("Кошелёк не найден", show_alert=True)
        return
    await query.answer("Удалено")
    rows = await db.list_wallets(uid)
    try:
        if not rows:
            await query.message.edit_text(
                "Кошелёк удалён. Список пуст - добавьте новый через «Добавить»",
                reply_markup=None,
            )
        else:
            await query.message.edit_text(
                "Выберите кошелёк для удаления:",
                reply_markup=_delete_kb(rows),
            )
    except Exception:
        if not rows:
            await query.message.answer(
                "Кошелёк удалён. Список пуст",
                reply_markup=main_menu_kb(),
            )
        else:
            await query.message.answer(
                "Выберите кошелёк для удаления:",
                reply_markup=_delete_kb(rows),
            )
