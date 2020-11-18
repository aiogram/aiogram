from typing import Dict, Tuple, Type

from .base import BaseFilter
from .command import Command, CommandObject
from .content_types import ContentTypesFilter
from .exception import ExceptionMessageFilter, ExceptionTypeFilter
from .text import Text

__all__ = (
    "BUILTIN_FILTERS",
    "BaseFilter",
    "Text",
    "Command",
    "CommandObject",
    "ContentTypesFilter",
    "ExceptionMessageFilter",
    "ExceptionTypeFilter",
)

BUILTIN_FILTERS: Dict[str, Tuple[Type[BaseFilter], ...]] = {
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
    "poll_answer": (),
    "error": (ExceptionMessageFilter, ExceptionTypeFilter),
}
