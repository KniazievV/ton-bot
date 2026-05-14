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
    # Mainnet base58 account addresses are 34 chars; TronGrid rejects shorter/longer paths.
    if not (a.startswith("T") and len(a) == 34):
        return False
    for ch in a:
        if ch not in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz":
            return False
    return True


def is_tron_mainnet_base58_address(addr: str) -> bool:
    """True if the string looks like a TRON mainnet base58 account (34 chars, T…)."""
    return _is_base58_tron_address(addr)


def _balance_from_trc20_balance_row(row: Any, contract: str) -> str | None:
    """TronGrid returns either legacy {balance: ...} or {CONTRACT_BASE58: balance_str}."""
    if not isinstance(row, dict):
        return None
    bal = row.get("balance")
    if bal is not None:
        return str(bal)
    bal = row.get(contract)
    if bal is not None:
        return str(bal)
    if len(row) == 1:
        v = next(iter(row.values()))
        if v is not None and isinstance(v, (str, int)):
            return str(v)
    return None


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
    headers = _headers()
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, params=params, headers=headers)
        # Wrong TRONGRID_API_KEY yields 401; public endpoint works without the header.
        if r.status_code == 401 and headers:
            r = await client.get(url, params=params, headers={})
        r.raise_for_status()
        data: dict[str, Any] = r.json()
    rows = data.get("data") or []
    if not rows:
        return "0"
    raw = _balance_from_trc20_balance_row(rows[0], USDT_TRC20_CONTRACT)
    if raw is None:
        return "0"
    return raw


def atomic_to_usdt_2dec(atomic: str) -> str:
    try:
        n = int(atomic)
    except ValueError:
        return atomic
    return f"{n / (10**USDT_DECIMALS):.2f}"

