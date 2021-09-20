from contextvars import ContextVar
from typing import Any, Optional

from aiogram.utils.i18n.babel import I18n
from aiogram.utils.i18n.lazy_proxy import LazyProxy

ctx_i18n: ContextVar[Optional[I18n]] = ContextVar("aiogram_ctx_i18n", default=None)


def get_i18n() -> I18n:
    i18n = ctx_i18n.get()
    if i18n is None:
        raise LookupError("I18n context is not set")
    return i18n


def gettext(*args: Any, **kwargs: Any) -> str:
    return get_i18n().gettext(*args, **kwargs)


def _lazy_lazy_gettext(*args: Any, **kwargs: Any) -> str:
    return str(get_i18n().lazy_gettext(*args, **kwargs))


def lazy_gettext(*args: Any, **kwargs: Any) -> LazyProxy:
    return LazyProxy(_lazy_lazy_gettext, *args, **kwargs)


ngettext = gettext
lazy_ngettext = lazy_gettext
