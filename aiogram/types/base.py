from typing import Any
from unittest.mock import sentinel

from pydantic import BaseModel, ConfigDict, GetCoreSchemaHandler
from pydantic_core import CoreSchema

from aiogram.client.context_controller import BotContextController
from aiogram.client.default import Default


def _fail_fast_lists(schema: Any, model: type[BaseModel]) -> None:
    """
    Make every list of the model's own core schema stop at the first invalid item.

    Otherwise pydantic keeps one error per item, each with the full location, so rejecting
    a nested update costs items x depth. Nested models are skipped: their own schema
    goes through this hook as well.
    """
    if isinstance(schema, dict):
        if schema.get("type") == "model" and schema.get("cls") is not model:
            return
        if schema.get("type") == "list":
            schema["fail_fast"] = True
        for value in schema.values():
            _fail_fast_lists(value, model)
    elif isinstance(schema, list):
        for value in schema:
            _fail_fast_lists(value, model)


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
    def __get_pydantic_core_schema__(
        cls,
        source: type[BaseModel],
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        schema = handler(source)
        _fail_fast_lists(schema, source)
        return schema


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
