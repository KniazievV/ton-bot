"""Курс TON к USDT через публичный API CoinGecko (без ключа)."""

from typing import Any

import httpx

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/the-open-network"


def _pct_line(label: str, value: Any) -> str:
    if value is None:
        return f"{label}: нет данных"
    try:
        x = float(value)
    except (TypeError, ValueError):
        return f"{label}: нет данных"
    if x > 0:
        return f"{label}: +{x:.2f}%"
    return f"{label}: {x:.2f}%"


async def fetch_ton_usdt_market() -> dict[str, Any]:
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(COINGECKO_URL, params=params)
        r.raise_for_status()
        data = r.json()
    md = data.get("market_data") or {}
    cp = md.get("current_price") or {}
    price = cp.get("usdt")
    if price is None:
        price = cp.get("usd")
    if price is None:
        raise RuntimeError("В ответе нет цены USDT/USD")
    return {
        "price": float(price),
        "pct_24h": md.get("price_change_percentage_24h"),
        "pct_7d": md.get("price_change_percentage_7d"),
        "pct_30d": md.get("price_change_percentage_30d"),
        "pct_1y": md.get("price_change_percentage_1y"),
    }


def format_ton_rate_message(m: dict[str, Any]) -> str:
    price = m["price"]
    lines = [
        f"Цена: <b>{price:.2f}</b> USDT",
        "",
        "Изменение цены:",
        _pct_line("за 24 часа", m.get("pct_24h")),
        _pct_line("за неделю", m.get("pct_7d")),
        _pct_line("за месяц", m.get("pct_30d")),
        _pct_line("за год", m.get("pct_1y")),
        "",
        "<i>Данные взяты с CoinGecko</i>",
    ]
    return "\n".join(lines)
