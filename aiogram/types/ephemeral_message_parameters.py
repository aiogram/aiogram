from typing import TYPE_CHECKING, Any

from .base import TelegramObject


class EphemeralMessageParameters(TelegramObject):
    """


    Source: https://core.telegram.org/bots/api#ephemeralmessageparameters
    """

    receiver_user_id: int
    """Identifier of the user who will receive the message. It is not guaranteed that the user will receive the message, especially if they are offline. See `here <https://core.telegram.org/bots/api#ephemeral-messages-and-commands>`_ for more details"""
    callback_query_id: str | None = None
    """*Optional*. Identifier of the callback query which triggered the message, if any"""
    replace_callback_query_message: bool | None = None
    """*Optional*. Pass :code:`True` if the ephemeral message must be shown in place of the original message. Must be :code:`False` for callback queries from ephemeral messages, which must be edited using regular *editEphemeralMessage…* methods"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            receiver_user_id: int,
            callback_query_id: str | None = None,
            replace_callback_query_message: bool | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                receiver_user_id=receiver_user_id,
                callback_query_id=callback_query_id,
                replace_callback_query_message=replace_callback_query_message,
                **__pydantic_kwargs,
            )
