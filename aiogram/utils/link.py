from typing import Any, Optional
from urllib.parse import urlencode, urljoin

BASE_DOCS_URL = "https://docs.aiogram.dev/"
BRANCH = "dev-3.x"

BASE_PAGE_URL = f"{BASE_DOCS_URL}/en/{BRANCH}/"


def _format_url(url: str, *path: str, fragment_: Optional[str] = None, **query: Any) -> str:
    url = urljoin(url, "/".join(path), allow_fragments=True)
    if query:
        url += "?" + urlencode(query)
    if fragment_:
        url += "#" + fragment_
    return url


def docs_url(*path: str, fragment_: Optional[str] = None, **query: Any) -> str:
    return _format_url(BASE_PAGE_URL, *path, fragment_=fragment_, **query)


def create_tg_link(link: str, **kwargs: Any) -> str:
    return _format_url(f"tg://{link}", **kwargs)


def create_telegram_link(*path: str, **kwargs: Any) -> str:
    return _format_url("https://t.me", *path, **kwargs)
