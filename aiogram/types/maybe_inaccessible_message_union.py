from __future__ import annotations

from typing import Union

from .inaccessible_message import InaccessibleMessage
from .message import Message

MaybeInaccessibleMessageUnion = Union[Message, InaccessibleMessage]
