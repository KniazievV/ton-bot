import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

import db
from config import TELEGRAM_BOT_TOKEN
from handlers import setup_routers
from monitor import balance_poll_loop
from web_health import run_healthcheck_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


async def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        log.error("Set TELEGRAM_BOT_TOKEN in .env")
        sys.exit(1)
    await db.init_db()
    bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(setup_routers())
    port_raw = os.environ.get("PORT", "").strip()

    @dp.message(Command("cancel"))
    async def cancel_fsm(message: Message, state: FSMContext) -> None:
        cur = await state.get_state()
        if cur is None:
            await message.answer("Нечего отменять")
            return
        await state.clear()
        from handlers.keyboards import main_menu_kb

        await message.answer("Ок, отменил текущее действие", reply_markup=main_menu_kb())

    asyncio.create_task(balance_poll_loop(bot))
    if port_raw.isdigit():
        asyncio.create_task(run_healthcheck_server(int(port_raw)))
    elif port_raw:
        log.warning("Invalid PORT value: %r", port_raw)
    log.info("Bot starting, poll interval %s s", __import__("config").POLL_INTERVAL_SEC)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
