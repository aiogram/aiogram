from typing import Dict, Tuple, Type

from .base import BaseFilter
from .command import Command, CommandObject
from .content_types import ContentTypesFilter
from .exception import ExceptionMessageFilter, ExceptionTypeFilter
from .state import StateFilter
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
    "StateFilter",
)

BUILTIN_FILTERS: Dict[str, Tuple[Type[BaseFilter], ...]] = {
    "message": (
        Text,
        Command,
        ContentTypesFilter,
        StateFilter,
    ),
    "edited_message": (
        Text,
        Command,
        ContentTypesFilter,
        StateFilter,
    ),
    "channel_post": (
        Text,
        ContentTypesFilter,
        StateFilter,
    ),
    "edited_channel_post": (
        Text,
        ContentTypesFilter,
        StateFilter,
    ),
    "inline_query": (
        Text,
        StateFilter,
    ),
    "chosen_inline_result": (StateFilter,),
    "callback_query": (
        Text,
        StateFilter,
    ),
    "shipping_query": (StateFilter,),
    "pre_checkout_query": (StateFilter,),
    "poll": (StateFilter,),
    "poll_answer": (StateFilter,),
    "my_chat_member": (StateFilter,),
    "chat_member": (StateFilter,),
    "error": (ExceptionMessageFilter, ExceptionTypeFilter),
}
