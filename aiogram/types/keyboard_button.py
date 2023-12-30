from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from pydantic import Field

from .base import MutableTelegramObject

if TYPE_CHECKING:
    from .keyboard_button_poll_type import KeyboardButtonPollType
    from .keyboard_button_request_chat import KeyboardButtonRequestChat
    from .keyboard_button_request_user import KeyboardButtonRequestUser
    from .keyboard_button_request_users import KeyboardButtonRequestUsers
    from .web_app_info import WebAppInfo


class KeyboardButton(MutableTelegramObject):
    """
    This object represents one button of the reply keyboard. For simple text buttons, *String* can be used instead of this object to specify the button text. The optional fields *web_app*, *request_users*, *request_chat*, *request_contact*, *request_location*, and *request_poll* are mutually exclusive.
    **Note:** *request_contact* and *request_location* options will only work in Telegram versions released after 9 April, 2016. Older clients will display *unsupported message*.

    **Note:** *request_poll* option will only work in Telegram versions released after 23 January, 2020. Older clients will display *unsupported message*.

    **Note:** *web_app* option will only work in Telegram versions released after 16 April, 2022. Older clients will display *unsupported message*.

    **Note:** *request_users* and *request_chat* options will only work in Telegram versions released after 3 February, 2023. Older clients will display *unsupported message*.

    Source: https://core.telegram.org/bots/api#keyboardbutton
    """

    text: str
    """Text of the button. If none of the optional fields are used, it will be sent as a message when the button is pressed"""
    request_users: Optional[KeyboardButtonRequestUsers] = None
    """*Optional.* If specified, pressing the button will open a list of suitable users. Identifiers of selected users will be sent to the bot in a 'users_shared' service message. Available in private chats only."""
    request_chat: Optional[KeyboardButtonRequestChat] = None
    """*Optional.* If specified, pressing the button will open a list of suitable chats. Tapping on a chat will send its identifier to the bot in a 'chat_shared' service message. Available in private chats only."""
    request_contact: Optional[bool] = None
    """*Optional*. If :code:`True`, the user's phone number will be sent as a contact when the button is pressed. Available in private chats only."""
    request_location: Optional[bool] = None
    """*Optional*. If :code:`True`, the user's current location will be sent when the button is pressed. Available in private chats only."""
    request_poll: Optional[KeyboardButtonPollType] = None
    """*Optional*. If specified, the user will be asked to create a poll and send it to the bot when the button is pressed. Available in private chats only."""
    web_app: Optional[WebAppInfo] = None
    """*Optional*. If specified, the described `Web App <https://core.telegram.org/bots/webapps>`_ will be launched when the button is pressed. The Web App will be able to send a 'web_app_data' service message. Available in private chats only."""
    request_user: Optional[KeyboardButtonRequestUser] = Field(
        None, json_schema_extra={"deprecated": True}
    )
    """*Optional.* If specified, pressing the button will open a list of suitable users. Tapping on any user will send their identifier to the bot in a 'user_shared' service message. Available in private chats only.

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            text: str,
            request_users: Optional[KeyboardButtonRequestUsers] = None,
            request_chat: Optional[KeyboardButtonRequestChat] = None,
            request_contact: Optional[bool] = None,
            request_location: Optional[bool] = None,
            request_poll: Optional[KeyboardButtonPollType] = None,
            web_app: Optional[WebAppInfo] = None,
            request_user: Optional[KeyboardButtonRequestUser] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                text=text,
                request_users=request_users,
                request_chat=request_chat,
                request_contact=request_contact,
                request_location=request_location,
                request_poll=request_poll,
                web_app=web_app,
                request_user=request_user,
                **__pydantic_kwargs,
            )
