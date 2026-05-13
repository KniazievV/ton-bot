from __future__ import annotations

from typing import Any

import httpx

from config import TRONGRID_API_KEY

TRONGRID_BASE = "https://api.trongrid.io"

# Official TRON USDT contract (TRC-20)
USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
USDT_DECIMALS = 6


def _headers() -> dict[str, str]:
    h: dict[str, str] = {}
    if TRONGRID_API_KEY:
        h["TRON-PRO-API-KEY"] = TRONGRID_API_KEY
    return h


def _is_base58_tron_address(addr: str) -> bool:
    a = addr.strip()
    if not (a.startswith("T") and 30 <= len(a) <= 40):
        return False
    # keep it light: just charset sanity; API will validate fully
    for ch in a:
        if ch not in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz":
            return False
    return True


async def fetch_usdt_trc20_balance_atomic(address: str) -> str:
    """
    Returns USDT (TRC-20) balance as integer string in atomic units (6 decimals).
    Uses TronGrid endpoint /v1/accounts/{address}/trc20/balance?contract_address=...
    """
    addr = address.strip()
    if not _is_base58_tron_address(addr):
        raise ValueError("Invalid TRON address")
    url = f"{TRONGRID_BASE}/v1/accounts/{addr}/trc20/balance"
    params = {"contract_address": USDT_TRC20_CONTRACT}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, params=params, headers=_headers())
        r.raise_for_status()
        data: dict[str, Any] = r.json()
    rows = data.get("data") or []
    if not rows:
        return "0"
    bal = rows[0].get("balance")
    if bal is None:
        return "0"
    return str(bal)


def atomic_to_usdt_2dec(atomic: str) -> str:
    try:
        n = int(atomic)
    except ValueError:
        return atomic
    return f"{n / (10**USDT_DECIMALS):.2f}"

