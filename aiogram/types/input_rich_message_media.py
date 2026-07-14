from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject

if TYPE_CHECKING:
    from .input_rich_message_media_union import InputRichMessageMediaUnion


class InputRichMessageMedia(TelegramObject):
    """
    Describes a media element embedded in an outgoing rich message.

    Source: https://core.telegram.org/bots/api#inputrichmessagemedia
    """

    id: str
    """Unique identifier of the media used in a :code:`tg://photo?id=`, :code:`tg://video?id=`, or :code:`tg://audio?id=` link. 1-64 characters, only :code:`A-Z`, :code:`a-z`, :code:`0-9`, :code:`_` and :code:`-` are allowed"""
    media: InputRichMessageMediaUnion
    """The media to be sent. Everything except the media itself and its properties is ignored"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: str,
            media: InputRichMessageMediaUnion,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(id=id, media=media, **__pydantic_kwargs)
