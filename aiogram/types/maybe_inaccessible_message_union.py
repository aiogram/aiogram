from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, TypeAlias

from pydantic import Discriminator, Tag
from typing_extensions import TypeAliasType

from .inaccessible_message import InaccessibleMessage
from .message import Message

if TYPE_CHECKING:
    MaybeInaccessibleMessageUnion: TypeAlias = Message | InaccessibleMessage
else:

    def _maybe_inaccessible_message_union_tag(value: Any) -> Any:
        value = value.get("date") if isinstance(value, dict) else getattr(value, "date", None)
        if value == 0:
            return "InaccessibleMessage"
        return "Message"

    MaybeInaccessibleMessageUnion = TypeAliasType(
        "MaybeInaccessibleMessageUnion",
        Annotated[
            Annotated[Message, Tag("Message")]
            | Annotated[InaccessibleMessage, Tag("InaccessibleMessage")],
            Discriminator(_maybe_inaccessible_message_union_tag),
        ],
    )
