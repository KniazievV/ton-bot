from typing import Any

import httpx

from config import TONCENTER_API_KEY, TONCENTER_BASE


def _headers() -> dict[str, str]:
    h: dict[str, str] = {}
    if TONCENTER_API_KEY:
        h["X-Api-Key"] = TONCENTER_API_KEY
    return h


def _params(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    p: dict[str, Any] = dict(extra or {})
    if TONCENTER_API_KEY:
        p["api_key"] = TONCENTER_API_KEY
    return p


def looks_like_ton_address(addr: str) -> bool:
    """Грубая проверка формата адреса TON (user-friendly EQ/UQ или raw workchain:hex)."""
    a = addr.strip()
    if a.startswith(("EQ", "UQ")) and 46 <= len(a) <= 96:
        return True
    if (a.startswith("0:") or a.startswith("-1:")) and 8 <= len(a) <= 128:
        return True
    return False


async def fetch_balance_nano(address: str) -> str:
    """Returns balance in nanoTON as decimal string. Raises on API/address error."""
    url = f"{TONCENTER_BASE}/getAddressInformation"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, params=_params({"address": address}), headers=_headers())
        r.raise_for_status()
        data = r.json()
    if not data.get("ok"):
        err = data.get("error") or data.get("description") or str(data)
        raise RuntimeError(err)
    result = data.get("result") or {}
    bal = result.get("balance")
    if bal is None:
        raise RuntimeError("No balance in response")
    return str(bal)


def nano_to_ton_display(nano: str) -> str:
    try:
        n = int(nano)
    except ValueError:
        return nano
    whole = n // 1_000_000_000
    frac = abs(n) % 1_000_000_000
    return f"{whole}.{frac:09d}".rstrip("0").rstrip(".")


def nano_to_ton_2dec(nano: str) -> str:
    try:
        n = int(nano)
    except ValueError:
        return nano
    return f"{n / 1_000_000_000:.2f}"
