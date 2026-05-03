import asyncio
import logging

from aiogram import Bot

import html

import db
from config import POLL_INTERVAL_SEC
from handlers.messaging import HIDE_LINK_PREVIEW
from ton_client import fetch_balance_nano, nano_to_ton_2dec
from wallet_links import address_link_html

log = logging.getLogger(__name__)


async def balance_poll_loop(bot: Bot) -> None:
    await asyncio.sleep(8)
    while True:
        try:
            wallets = await db.all_wallets_for_poll()
            for w in wallets:
                wid = w["id"]
                uid = w["user_id"]
                addr = w["address"]
                title = w.get("display_name") or "—"
                notify = bool(w["notify"])
                try:
                    old = int(str(w["last_balance_nano"]))
                except ValueError:
                    old = 0
                try:
                    new_s = await fetch_balance_nano(addr)
                    new = int(new_s)
                except Exception:
                    log.exception("TON poll failed for wallet %s", wid)
                    continue
                if new > old and notify:
                    delta = new - old
                    try:
                        await bot.send_message(
                            uid,
                            "Пополнение на кошельке TON\n\n"
                            f"Имя: <b>{html.escape(str(title))}</b>\n"
                            f"Адрес: {address_link_html(addr)}\n"
                            f"Было: {nano_to_ton_2dec(str(old))} TON\n"
                            f"Стало: {nano_to_ton_2dec(str(new))} TON\n"
                            f"<b>+{nano_to_ton_2dec(str(delta))} TON</b>",
                            link_preview_options=HIDE_LINK_PREVIEW,
                        )
                    except Exception:
                        log.exception("Failed to notify user %s", uid)
                if new != old:
                    await db.update_balance(wid, str(new))
        except Exception:
            log.exception("balance_poll_loop tick failed")
        await asyncio.sleep(POLL_INTERVAL_SEC)
