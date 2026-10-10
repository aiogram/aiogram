from __future__ import annotations

from typing import Any

from aiogram.utils.i18n.core import I18n
from aiogram.utils.i18n.lazy_proxy import LazyProxy


def get_i18n() -> I18n:
    i18n = I18n.get_current(no_error=True)
    if i18n is None:
        msg = "I18n context is not set"
        raise LookupError(msg)
    return i18n


def gettext(*args: Any, **kwargs: Any) -> str:
    return get_i18n().gettext(*args, **kwargs)


def lazy_gettext(*args: Any, **kwargs: Any) -> LazyProxy:
    return LazyProxy(gettext, *args, **kwargs, enable_cache=False)


def pgettext(
    context: str,
    singular: str,
    plural: str | None = None,
    n: int = 1,
    locale: str | None = None,
) -> str:
    return get_i18n().gettext(singular, plural=plural, n=n, locale=locale, context=context)


def lazy_pgettext(
    context: str,
    singular: str,
    plural: str | None = None,
    n: int = 1,
    locale: str | None = None,
) -> LazyProxy:
    return LazyProxy(
        pgettext,
        context,
        singular,
        plural=plural,
        n=n,
        locale=locale,
        enable_cache=False,
    )


ngettext = gettext
lazy_ngettext = lazy_gettext
npgettext = pgettext
lazy_npgettext = lazy_pgettext
