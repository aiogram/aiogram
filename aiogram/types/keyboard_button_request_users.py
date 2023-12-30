from typing import TYPE_CHECKING, Any, Optional

from aiogram.types import TelegramObject


class KeyboardButtonRequestUsers(TelegramObject):
    """
    This object defines the criteria used to request suitable users. The identifiers of the selected users will be shared with the bot when the corresponding button is pressed. `More about requesting users » <https://core.telegram.org/bots/features#chat-and-user-selection>`_

    Source: https://core.telegram.org/bots/api#keyboardbuttonrequestusers
    """

    request_id: int
    """Signed 32-bit identifier of the request that will be received back in the :class:`aiogram.types.users_shared.UsersShared` object. Must be unique within the message"""
    user_is_bot: Optional[bool] = None
    """*Optional*. Pass :code:`True` to request bots, pass :code:`False` to request regular users. If not specified, no additional restrictions are applied."""
    user_is_premium: Optional[bool] = None
    """*Optional*. Pass :code:`True` to request premium users, pass :code:`False` to request non-premium users. If not specified, no additional restrictions are applied."""
    max_quantity: Optional[int] = None
    """*Optional*. The maximum number of users to be selected; 1-10. Defaults to 1."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            request_id: int,
            user_is_bot: Optional[bool] = None,
            user_is_premium: Optional[bool] = None,
            max_quantity: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                request_id=request_id,
                user_is_bot=user_is_bot,
                user_is_premium=user_is_premium,
                max_quantity=max_quantity,
                **__pydantic_kwargs,
            )
