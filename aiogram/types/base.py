from typing import Any, Dict, Union
from unittest.mock import sentinel

from pydantic import (
    BaseModel,
    ConfigDict,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from aiogram.client.context_controller import BotContextController
from aiogram.client.default import Default, DefaultBotProperties


class TelegramObject(BotContextController, BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        extra="allow",
        validate_assignment=True,
        frozen=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        defer_build=True,
    )

    @model_validator(mode="before")
    @classmethod
    def remove_unset(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove UNSET before fields validation.

        We use UNSET as a sentinel value for `parse_mode` and replace it to real value later.
        It isn't a problem when it's just default value for a model field,
        but UNSET might be passed to a model initialization from `Bot.method_name`,
        so we must take care of it and remove it before fields validation.
        """
        if not isinstance(values, dict):
            return values
        return {k: v for k, v in values.items() if not isinstance(v, UNSET_TYPE)}

    @model_serializer(mode="wrap", when_used="json")
    def json_serialize(
        self, serializer: SerializerFunctionWrapHandler
    ) -> Union[Dict[str, Any], Any]:
        """
        Replacing `Default` placeholders with actual values from bot defaults.
        Ensures JSON serialization backward compatibility by handling non-standard objects.
        """
        if not isinstance(self, TelegramObject):
            return serializer(self)  # Can be passed when using Union[Any, TelegramObject]
        properties = self.bot.default if self.bot else DefaultBotProperties()
        default_fields = {
            key: properties[value.name] for key, value in self if isinstance(value, Default)
        }
        return serializer(self.model_copy(update=default_fields))


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
