import html
from urllib.parse import quote

# Публичная страница кошелька в Tonviewer
_TONVIEWER = "https://tonviewer.com/{}"


def short_address(addr: str, head: int = 3, tail: int = 3) -> str:
    a = addr.strip()
    if len(a) <= head + tail + 1:
        return a
    return f"{a[:head]}…{a[-tail:]}"


def address_link_html(addr: str) -> str:
    a = addr.strip()
    url = _TONVIEWER.format(quote(a, safe=""))
    label = html.escape(short_address(a))
    return f'<a href="{html.escape(url)}">{label}</a>'
