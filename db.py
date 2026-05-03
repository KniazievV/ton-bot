import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "wallets.db"


async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                address TEXT NOT NULL,
                display_name TEXT NOT NULL,
                notify INTEGER NOT NULL DEFAULT 1,
                last_balance_nano TEXT NOT NULL DEFAULT '0',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, address)
            )
            """
        )
        await db.commit()


async def wallet_exists_for_user(user_id: int, address: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM wallets WHERE user_id = ? AND address = ? LIMIT 1",
            (user_id, address.strip()),
        )
        return (await cur.fetchone()) is not None


async def add_wallet(
    user_id: int,
    address: str,
    display_name: str,
    notify: bool,
    initial_balance_nano: str,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO wallets (user_id, address, display_name, notify, last_balance_nano)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, address.strip(), display_name.strip(), 1 if notify else 0, initial_balance_nano),
        )
        await db.commit()


async def list_wallets(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT id, address, display_name, notify, last_balance_nano
            FROM wallets
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def all_wallets_for_poll() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT id, user_id, address, display_name, notify, last_balance_nano
            FROM wallets
            """
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def delete_all_wallets_for_user(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM wallets WHERE user_id = ?", (user_id,))
        await db.commit()
        cur = await db.execute("SELECT changes()")
        return int((await cur.fetchone())[0])


async def delete_wallet(user_id: int, wallet_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM wallets WHERE id = ? AND user_id = ?",
            (wallet_id, user_id),
        )
        await db.commit()
        cur = await db.execute("SELECT changes()")
        n = (await cur.fetchone())[0]
        return int(n) > 0


async def update_balance(wallet_id: int, balance_nano: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE wallets SET last_balance_nano = ? WHERE id = ?",
            (balance_nano, wallet_id),
        )
        await db.commit()
