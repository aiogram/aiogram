from typing import Any
from unittest.mock import sentinel

from pydantic import BaseModel, ConfigDict

from aiogram.utils.mixins import ContextInstanceMixin


class TelegramObject(ContextInstanceMixin["TelegramObject"], BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        extra="allow",
        validate_assignment=True,
        frozen=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class MutableTelegramObject(TelegramObject):
    model_config = ConfigDict(
        frozen=False,
    )


# special sentinel object which used in situation when None might be a useful value
UNSET_PARSE_MODE: Any = sentinel.UNSET_PARSE_MODE
UNSET_DISABLE_WEB_PAGE_PREVIEW = sentinel.UNSET_DISABLE_WEB_PAGE_PREVIEW
UNSET_PROTECT_CONTENT = sentinel.UNSET_PROTECT_CONTENT
UNSET_TYPE = type(sentinel.DEFAULT)
