from typing import Any
from urllib.parse import urlencode, urljoin


def create_tg_link(link: str, **kwargs: Any) -> str:
    url = f"tg://{link}"
    if kwargs:
        query = urlencode(kwargs)
        url += f"?{query}"
    return url


def create_telegram_link(uri: str, **kwargs: Any) -> str:
    url = urljoin("https://t.me", uri)
    if kwargs:
        query = urlencode(query=kwargs)
        url += f"?{query}"
    return url
