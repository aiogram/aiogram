from __future__ import annotations

from enum import Enum
from typing import Union

from aiogram.api.types import (
    CallbackQuery,
    ChosenInlineResult,
    InlineQuery,
    Message,
    Poll,
    PollAnswer,
    PreCheckoutQuery,
    ShippingQuery,
    Update,
)

UpdateType = Union[
    CallbackQuery,
    ChosenInlineResult,
    InlineQuery,
    Message,
    Poll,
    PollAnswer,
    PreCheckoutQuery,
    ShippingQuery,
    Update,
]


class MiddlewareStep(Enum):
    PRE_PROCESS = "pre_process"
    PROCESS = "process"
    POST_PROCESS = "post_process"
