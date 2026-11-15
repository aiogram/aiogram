from typing import TYPE_CHECKING, Any

from .base import TelegramObject


class EphemeralMessageParameters(TelegramObject):
    """


    Source: https://core.telegram.org/bots/api#ephemeralmessageparameters
    """

    receiver_user_id: int | None = None
    """*Optional*. Identifier of the user who will receive the message; required unless the message is sent as an ephemeral reply to a callback query. If omitted, then the parameter *chat_id* of the method is ignored. If specified together with *callback_query_id*, then it must be the identifier of the user who pressed the button. Must be omitted for messages sent in chats where the bot isn't a member, unless the message is a reply to an ephemeral message. It is not guaranteed that the user will receive the message, especially if they are offline. See `here <https://core.telegram.org/bots/api#ephemeral-messages-and-commands>`_ for more details"""
    callback_query_id: str | None = None
    """*Optional*. Identifier of the callback query which triggered the message, if any. If specified and *receiver_user_id* is omitted, then the message is sent as an ephemeral reply to the callback query and will be shown only to the user who pressed the button. Ephemeral replies can't be sent to callback queries from messages in channel direct messages chats. The bot must still answer the callback query using :class:`aiogram.methods.answer_callback_query.AnswerCallbackQuery`"""
    replace_callback_query_message: bool | None = None
    """*Optional*. Pass :code:`True` if the ephemeral message must be shown in place of the original message. Must be :code:`False` for callback queries from ephemeral messages, which must be edited using regular *editEphemeralMessage…* methods"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            receiver_user_id: int | None = None,
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
