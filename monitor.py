import asyncio
import logging

from aiogram import Bot

import html

import db
from config import POLL_INTERVAL_SEC
from handlers.messaging import HIDE_LINK_PREVIEW
from ton_client import fetch_balance_nano, nano_to_ton_2dec
from tron_client import atomic_to_usdt_2dec, fetch_usdt_trc20_balance_atomic
from wallet_links import address_link_html_by_chain

log = logging.getLogger(__name__)


async def balance_poll_loop(bot: Bot) -> None:
    await asyncio.sleep(8)
    while True:
        try:
            wallets = await db.all_wallets_for_poll()
            for w in wallets:
                wid = w["id"]
                uid = w["user_id"]
                chain = (w.get("chain") or "TON").strip().upper()
                addr = w["address"]
                title = w.get("display_name") or "—"
                notify = bool(w["notify"])
                try:
                    old = int(str(w["last_balance_nano"]))
                except ValueError:
                    old = 0
                try:
                    if chain == "TRON":
                        new_s = await fetch_usdt_trc20_balance_atomic(addr)
                    else:
                        new_s = await fetch_balance_nano(addr)
                    new = int(str(new_s))
                except Exception:
                    log.exception("%s poll failed for wallet %s", chain, wid)
                    continue
                if new > old and notify:
                    delta = new - old
                    if chain == "TRON":
                        old_s = atomic_to_usdt_2dec(str(old))
                        new_s2 = atomic_to_usdt_2dec(str(new))
                        delta_s = atomic_to_usdt_2dec(str(delta))
                        unit = "USDT"
                        title_line = "Пополнение на кошельке TRON (USDT TRC-20)"
                    else:
                        old_s = nano_to_ton_2dec(str(old))
                        new_s2 = nano_to_ton_2dec(str(new))
                        delta_s = nano_to_ton_2dec(str(delta))
                        unit = "TON"
                        title_line = "Пополнение на кошельке TON"
                    try:
                        await bot.send_message(
                            uid,
                            f"{title_line}\n\n"
                            f"Имя: <b>{html.escape(str(title))}</b>\n"
                            f"Адрес: {address_link_html_by_chain(chain, addr)}\n"
                            f"Было: {old_s} {unit}\n"
                            f"Стало: {new_s2} {unit}\n"
                            f"<b>+{delta_s} {unit}</b>",
                            link_preview_options=HIDE_LINK_PREVIEW,
                        )
                    except Exception:
                        log.exception("Failed to notify user %s", uid)
                if new != old:
                    await db.update_balance(wid, str(new))
        except Exception:
            log.exception("balance_poll_loop tick failed")
        await asyncio.sleep(POLL_INTERVAL_SEC)
