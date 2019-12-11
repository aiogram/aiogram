from typing import Dict, Tuple, Union

from .base import BaseFilter
from .command import Command, CommandObject
from .content_types import ContentTypesFilter
from .text import Text

__all__ = (
    "BUILTIN_FILTERS",
    "BaseFilter",
    "Text",
    "Command",
    "CommandObject",
    "ContentTypesFilter",
)

BUILTIN_FILTERS: Dict[str, Union[Tuple[BaseFilter], Tuple]] = {
    "update": (),
    "message": (Text, Command, ContentTypesFilter),
    "edited_message": (Text, Command, ContentTypesFilter),
    "channel_post": (Text, ContentTypesFilter),
    "edited_channel_post": (Text, ContentTypesFilter),
    "inline_query": (Text,),
    "chosen_inline_result": (),
    "callback_query": (Text,),
    "shipping_query": (),
    "pre_checkout_query": (),
    "poll": (),
}
