from typing import TYPE_CHECKING, Any

from .base import TelegramMethod


class SetMySettings(TelegramMethod[bool]):
    """
    Use this method to change settings of the bot. Settings that aren't specified remain unchanged. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setmysettings
    """

    __returning__ = bool
    __api_method__ = "setMySettings"

    supports_inline_queries: bool | None = None
    """Pass :code:`True` to enable `inline mode <https://core.telegram.org/bots/api#inline-mode>`_ for the bot or :code:`False` to disable it"""
    inline_query_placeholder: str | None = None
    """New placeholder for inline queries, which is shown in the input field after the bot's username. Pass an empty string to use the default placeholder"""
    needs_inline_query_location: bool | None = None
    """Pass :code:`True` to request the location of the user with every inline query to the bot or :code:`False` to stop requesting it"""
    inline_feedback_share_denominator: int | None = None
    """Denominator of the share of `chosen inline results <https://core.telegram.org/bots/api#choseninlineresult>`_ received by the bot; the bot receives 1 out of *inline_feedback_share_denominator* chosen results. Must be one of 1, 10, 100, or 1000. Pass 0 to stop receiving chosen inline results"""
    can_join_groups: bool | None = None
    """Pass :code:`True` to allow adding the bot to groups or :code:`False` to disallow it"""
    can_read_all_group_messages: bool | None = None
    """Pass :code:`True` to disable `privacy mode <https://core.telegram.org/bots/features#privacy-mode>`_ for the bot or :code:`False` to enable it"""
    can_connect_to_business: bool | None = None
    """Pass :code:`True` to allow connecting the bot to user accounts to manage them or :code:`False` to disallow it"""
    can_manage_bots: bool | None = None
    """Pass :code:`True` to allow creating other bots that will be controlled by the bot or :code:`False` to disallow it"""
    supports_guest_queries: bool | None = None
    """Pass :code:`True` to allow guest queries to the bot from chats it isn't a member of or :code:`False` to disallow them"""
    supports_join_request_queries: bool | None = None
    """Pass :code:`True` to allow assigning the bot to process join request queries or :code:`False` to disallow it"""
    has_topics_enabled: bool | None = None
    """Pass :code:`True` to enable forum topic mode in private chats with the bot or :code:`False` to disable it"""
    allows_users_to_create_topics: bool | None = None
    """Pass :code:`True` to allow users to create and delete topics in private chats with the bot or :code:`False` to disallow it"""
    has_topic_sidebar: bool | None = None
    """Pass :code:`True` to show topics in private chats with the bot in a sidebar or :code:`False` to stop showing them in a sidebar"""
    can_communicate_with_bots: bool | None = None
    """Pass :code:`True` to allow the bot to communicate with other bots in groups, private chats, and through business accounts or :code:`False` to disallow it"""
    callback_query_mode: str | None = None
    """Mode in which the bot receives `callback queries <https://core.telegram.org/bots/api#callbackquery>`_ from buttons in messages sent by the bot. Must be one of 'default' (the field *message* is always used and contains an :class:`aiogram.types.inaccessible_message.InaccessibleMessage` if the message is inaccessible to the bot), 'auto' (the field *inline_message_id* is used instead of the field *message* if the message is inaccessible to the bot; the field *message* can still contain an inaccessible message if the message has just been deleted), or 'inline' (the field *inline_message_id* is always used instead of the field *message*)"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            supports_inline_queries: bool | None = None,
            inline_query_placeholder: str | None = None,
            needs_inline_query_location: bool | None = None,
            inline_feedback_share_denominator: int | None = None,
            can_join_groups: bool | None = None,
            can_read_all_group_messages: bool | None = None,
            can_connect_to_business: bool | None = None,
            can_manage_bots: bool | None = None,
            supports_guest_queries: bool | None = None,
            supports_join_request_queries: bool | None = None,
            has_topics_enabled: bool | None = None,
            allows_users_to_create_topics: bool | None = None,
            has_topic_sidebar: bool | None = None,
            can_communicate_with_bots: bool | None = None,
            callback_query_mode: str | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                supports_inline_queries=supports_inline_queries,
                inline_query_placeholder=inline_query_placeholder,
                needs_inline_query_location=needs_inline_query_location,
                inline_feedback_share_denominator=inline_feedback_share_denominator,
                can_join_groups=can_join_groups,
                can_read_all_group_messages=can_read_all_group_messages,
                can_connect_to_business=can_connect_to_business,
                can_manage_bots=can_manage_bots,
                supports_guest_queries=supports_guest_queries,
                supports_join_request_queries=supports_join_request_queries,
                has_topics_enabled=has_topics_enabled,
                allows_users_to_create_topics=allows_users_to_create_topics,
                has_topic_sidebar=has_topic_sidebar,
                can_communicate_with_bots=can_communicate_with_bots,
                callback_query_mode=callback_query_mode,
                **__pydantic_kwargs,
            )
