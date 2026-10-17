from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject

if TYPE_CHECKING:
    from .copy_text_button import CopyTextButton
    from .disabled_button import DisabledButton
    from .login_url import LoginUrl
    from .rich_text_union import RichTextUnion
    from .switch_inline_query_chosen_chat import SwitchInlineQueryChosenChat
    from .web_app_info import WebAppInfo


class RichMessageButton(TelegramObject):
    """
    This object represents a button in a :class:`aiogram.types.rich_message.RichMessage`. Exactly one of the fields other than *text* and *style* must be used to specify the type of the button.

    Source: https://core.telegram.org/bots/api#richmessagebutton
    """

    text: RichTextUnion
    """Text of the button. May contain only plain text, :class:`aiogram.types.rich_text_custom_emoji.RichTextCustomEmoji` and :class:`aiogram.types.rich_text_date_time.RichTextDateTime` entities"""
    style: str | None = None
    """*Optional*. Style of the button. Must be one of 'danger' (red), 'success' (green), 'primary' (blue) or 'link' (the button is shown as a regular link without borders). If omitted, then an app-specific style is used. The style 'link' is allowed only for callback buttons"""
    url: str | None = None
    """*Optional*. HTTP or tg:// URL to be opened when the button is pressed. Links :code:`tg://user?id=<user_id>` can be used to mention a user by their identifier without using a username, if this is allowed by their privacy settings"""
    callback_data: str | None = None
    """*Optional*. Data to be sent in a `callback query <https://core.telegram.org/bots/api#callbackquery>`_ to the bot when the button is pressed, 1-64 bytes"""
    web_app: WebAppInfo | None = None
    """*Optional*. Description of the `Web App <https://core.telegram.org/bots/webapps>`_ that will be launched when the user presses the button. The Web App will be able to send an arbitrary message on behalf of the user using the method :class:`aiogram.methods.answer_web_app_query.AnswerWebAppQuery`. Available only in private chats between a user and the bot. Not supported for messages sent on behalf of a business account"""
    login_url: LoginUrl | None = None
    """*Optional*. An HTTPS URL used to automatically authorize the user. Can be used as a replacement for the `Telegram Login Widget <https://core.telegram.org/widgets/login>`_. Not supported for ephemeral messages"""
    switch_inline_query: str | None = None
    """*Optional*. If set, pressing the button will prompt the user to select one of their chats, open that chat and insert the bot's username and the specified inline query in the input field. May be empty, in which case just the bot's username will be inserted. Not supported for messages sent in channel direct messages chats and on behalf of a business account"""
    switch_inline_query_current_chat: str | None = None
    """*Optional*. If set, pressing the button will insert the bot's username and the specified inline query in the current chat's input field. May be empty, in which case only the bot's username will be inserted. Not supported in channels and for messages sent in channel direct messages chats and on behalf of a business account"""
    switch_inline_query_chosen_chat: SwitchInlineQueryChosenChat | None = None
    """*Optional*. If set, pressing the button will prompt the user to select one of their chats of the specified type, open that chat and insert the bot's username and the specified inline query in the input field. Not supported for messages sent in channel direct messages chats and on behalf of a business account"""
    copy_text: CopyTextButton | None = None
    """*Optional*. A button that copies the specified text to the clipboard"""
    disabled: DisabledButton | None = None
    """*Optional*. If set, then the button is disabled and does nothing"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            text: RichTextUnion,
            style: str | None = None,
            url: str | None = None,
            callback_data: str | None = None,
            web_app: WebAppInfo | None = None,
            login_url: LoginUrl | None = None,
            switch_inline_query: str | None = None,
            switch_inline_query_current_chat: str | None = None,
            switch_inline_query_chosen_chat: SwitchInlineQueryChosenChat | None = None,
            copy_text: CopyTextButton | None = None,
            disabled: DisabledButton | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                text=text,
                style=style,
                url=url,
                callback_data=callback_data,
                web_app=web_app,
                login_url=login_url,
                switch_inline_query=switch_inline_query,
                switch_inline_query_current_chat=switch_inline_query_current_chat,
                switch_inline_query_chosen_chat=switch_inline_query_chosen_chat,
                copy_text=copy_text,
                disabled=disabled,
                **__pydantic_kwargs,
            )
