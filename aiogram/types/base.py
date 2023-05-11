from typing import Any
from unittest.mock import sentinel

import msgspec

from aiogram.utils.mixins import ContextInstanceMixin


class TelegramObject(
    ContextInstanceMixin["TelegramObject"], msgspec.Struct, omit_defaults=True, weakref=True
):
    ...


class MutableTelegramObject(TelegramObject):
    ...


# special sentinel object which used in situation when None might be a useful value
UNSET_PARSE_MODE: Any = sentinel.UNSET_PARSE_MODE
UNSET_DISABLE_WEB_PAGE_PREVIEW = sentinel.UNSET_DISABLE_WEB_PAGE_PREVIEW
UNSET_PROTECT_CONTENT = sentinel.UNSET_PROTECT_CONTENT
UNSET_TYPE = type(sentinel.DEFAULT)
