from typing import Dict, Tuple, Type

from .base import BaseFilter
from .command import Command, CommandObject
from .content_types import ContentTypesFilter
from .exception import ExceptionMessageFilter, ExceptionTypeFilter
from .magic_data import MagicData
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
    "MagicData",
)

_ALL_EVENTS_FILTERS: Tuple[Type[BaseFilter], ...] = (MagicData,)
_TELEGRAM_EVENTS_FILTERS: Tuple[Type[BaseFilter], ...] = (StateFilter,)

BUILTIN_FILTERS: Dict[str, Tuple[Type[BaseFilter], ...]] = {
    "message": (
        Text,
        Command,
        ContentTypesFilter,
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "edited_message": (
        Text,
        Command,
        ContentTypesFilter,
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "channel_post": (
        Text,
        ContentTypesFilter,
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "edited_channel_post": (
        Text,
        ContentTypesFilter,
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "inline_query": (
        Text,
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "chosen_inline_result": (
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "callback_query": (
        Text,
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "shipping_query": (
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "pre_checkout_query": (
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "poll": (
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "poll_answer": (
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "my_chat_member": (
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "chat_member": (
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "chat_join_request": (
        *_ALL_EVENTS_FILTERS,
        *_TELEGRAM_EVENTS_FILTERS,
    ),
    "error": (
        ExceptionMessageFilter,
        ExceptionTypeFilter,
        *_ALL_EVENTS_FILTERS,
    ),
}
