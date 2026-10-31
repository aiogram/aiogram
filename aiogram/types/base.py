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

    @classmethod
    def remove_unset(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Remove UNSET from a mapping before it is passed to field validation.

        Kept as a helper for external code, but no longer registered as a
        ``model_validator(mode="before")``: Telegram never sends UNSET, and a
        before-validator makes pydantic build an intermediate dict and call back
        into Python for every model of a nested update, which also defeats
        :meth:`pydantic.BaseModel.model_validate_json`. UNSET only reaches
        outbound models, where :class:`aiogram.methods.base.TelegramMethod`
        still strips it.
        """
        if not isinstance(values, dict):
            return values
        return {k: v for k, v in values.items() if not isinstance(v, UNSET_TYPE)}


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
