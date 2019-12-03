from typing import Dict, Tuple, Union

from .base import BaseFilter
from .command import Command, CommandObject
from .text import Text

__all__ = ("BUILTIN_FILTERS", "BaseFilter", "Text", "Command", "CommandObject")

BUILTIN_FILTERS: Dict[str, Union[Tuple[BaseFilter], Tuple]] = {
    "update": (),
    "message": (Text, Command),
    "edited_message": (Text, Command),
    "channel_post": (Text,),
    "edited_channel_post": (Text,),
    "inline_query": (Text,),
    "chosen_inline_result": (),
    "callback_query": (Text,),
    "shipping_query": (),
    "pre_checkout_query": (),
    "poll": (),
}
