from typing import Any
from unittest.mock import sentinel

from pydantic import BaseModel, ConfigDict

from aiogram.client.context_controller import BotContextController
from aiogram.client.default import Default


class TelegramObject(BotContextController, BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        extra="allow",
        validate_assignment=True,
        frozen=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        defer_build=True,
        protected_namespaces=(),
    )


class MutableTelegramObject(TelegramObject):
    model_config = ConfigDict(
        frozen=False,
    )


# special sentinel object which used in a situation when None might be a useful value
UNSET: Any = sentinel.UNSET
UNSET_TYPE: Any = type(UNSET)

# Unused constants are needed only for backward compatibility with external
# libraries that a working with framework internals
UNSET_PARSE_MODE: Any = Default("parse_mode")
UNSET_DISABLE_WEB_PAGE_PREVIEW: Any = Default("link_preview_is_disabled")
UNSET_PROTECT_CONTENT: Any = Default("protect_content")
