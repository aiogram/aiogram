from typing import Dict, Tuple, Union

from .base import BaseFilter
from .text import Text

__all__ = ("BUILTIN_FILTERS", "BaseFilter", "Text")

BUILTIN_FILTERS: Dict[str, Union[Tuple[BaseFilter], Tuple]] = {
    "update": (),
    "message": (Text,),
    "edited_message": (Text,),
    "channel_post": (Text,),
    "edited_channel_post": (Text,),
    "inline_query": (Text,),
    "chosen_inline_result": (),
    "callback_query": (Text,),
    "shipping_query": (),
    "pre_checkout_query": (),
    "poll": (),
}
