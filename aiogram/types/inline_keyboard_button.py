from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import MutableTelegramObject

if TYPE_CHECKING:
    from .callback_game import CallbackGame
    from .login_url import LoginUrl
    from .switch_inline_query_chosen_chat import SwitchInlineQueryChosenChat
    from .web_app_info import WebAppInfo


class InlineKeyboardButton(MutableTelegramObject):
    """
    This object represents one button of an inline keyboard. You **must** use exactly one of the optional fields.

    Source: https://core.telegram.org/bots/api#inlinekeyboardbutton
    """

    text: str
    """Label text on the button"""
    url: Optional[str] = None
    """*Optional*. HTTP or tg:// URL to be opened when the button is pressed. Links :code:`tg://user?id=<user_id>` can be used to mention a user by their identifier without using a username, if this is allowed by their privacy settings."""
    callback_data: Optional[str] = None
    """*Optional*. Data to be sent in a `callback query <https://core.telegram.org/bots/api#callbackquery>`_ to the bot when button is pressed, 1-64 bytes. Not supported for messages sent on behalf of a Telegram Business account."""
    web_app: Optional[WebAppInfo] = None
    """*Optional*. Description of the `Web App <https://core.telegram.org/bots/webapps>`_ that will be launched when the user presses the button. The Web App will be able to send an arbitrary message on behalf of the user using the method :class:`aiogram.methods.answer_web_app_query.AnswerWebAppQuery`. Available only in private chats between a user and the bot. Not supported for messages sent on behalf of a Telegram Business account."""
    login_url: Optional[LoginUrl] = None
    """*Optional*. An HTTPS URL used to automatically authorize the user. Can be used as a replacement for the `Telegram Login Widget <https://core.telegram.org/widgets/login>`_."""
    switch_inline_query: Optional[str] = None
    """*Optional*. If set, pressing the button will prompt the user to select one of their chats, open that chat and insert the bot's username and the specified inline query in the input field. May be empty, in which case just the bot's username will be inserted. Not supported for messages sent on behalf of a Telegram Business account."""
    switch_inline_query_current_chat: Optional[str] = None
    """*Optional*. If set, pressing the button will insert the bot's username and the specified inline query in the current chat's input field. May be empty, in which case only the bot's username will be inserted."""
    switch_inline_query_chosen_chat: Optional[SwitchInlineQueryChosenChat] = None
    """*Optional*. If set, pressing the button will prompt the user to select one of their chats of the specified type, open that chat and insert the bot's username and the specified inline query in the input field. Not supported for messages sent on behalf of a Telegram Business account."""
    callback_game: Optional[CallbackGame] = None
    """*Optional*. Description of the game that will be launched when the user presses the button."""
    pay: Optional[bool] = None
    """*Optional*. Specify :code:`True`, to send a `Pay button <https://core.telegram.org/bots/api#payments>`_."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            text: str,
            url: Optional[str] = None,
            callback_data: Optional[str] = None,
            web_app: Optional[WebAppInfo] = None,
            login_url: Optional[LoginUrl] = None,
            switch_inline_query: Optional[str] = None,
            switch_inline_query_current_chat: Optional[str] = None,
            switch_inline_query_chosen_chat: Optional[SwitchInlineQueryChosenChat] = None,
            callback_game: Optional[CallbackGame] = None,
            pay: Optional[bool] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                text=text,
                url=url,
                callback_data=callback_data,
                web_app=web_app,
                login_url=login_url,
                switch_inline_query=switch_inline_query,
                switch_inline_query_current_chat=switch_inline_query_current_chat,
                switch_inline_query_chosen_chat=switch_inline_query_chosen_chat,
                callback_game=callback_game,
                pay=pay,
                **__pydantic_kwargs,
            )
