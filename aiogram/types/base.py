from typing import Any
from unittest.mock import sentinel

from pydantic import BaseModel, ConfigDict

from aiogram.client.context_controller import BotContextController


class TelegramObject(BotContextController, BaseModel):
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
UNSET: Any = sentinel.UNSET
UNSET_PARSE_MODE: Any = sentinel.UNSET_PARSE_MODE
UNSET_DISABLE_WEB_PAGE_PREVIEW: Any = sentinel.UNSET_DISABLE_WEB_PAGE_PREVIEW
UNSET_PROTECT_CONTENT: Any = sentinel.UNSET_PROTECT_CONTENT
UNSET_TYPE: Any = type(UNSET)
