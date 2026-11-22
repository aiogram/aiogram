from typing import TYPE_CHECKING, Any

from .base import TelegramObject


class BotFullInfo(TelegramObject):
    """
    This object contains full information about the bot itself.

    Source: https://core.telegram.org/bots/api#botfullinfo
    """

    id: int
    """Unique identifier for this bot. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a 64-bit integer or double-precision float type are safe for storing this identifier"""
    is_bot: bool
    """Always :code:`True`"""
    first_name: str
    """Bot's first name"""
    can_join_groups: bool
    """:code:`True`, if the bot can be added to groups"""
    can_read_all_group_messages: bool
    """:code:`True`, if `privacy mode <https://core.telegram.org/bots/features#privacy-mode>`_ is disabled for the bot"""
    supports_guest_queries: bool
    """:code:`True`, if the bot supports guest queries from chats it is not a member of"""
    supports_inline_queries: bool
    """:code:`True`, if the bot supports inline queries"""
    needs_inline_query_location: bool
    """:code:`True`, if the bot requests the location of the user with every inline query"""
    can_connect_to_business: bool
    """:code:`True`, if the bot can be connected to a user account to manage it"""
    has_main_web_app: bool
    """:code:`True`, if the bot has a main Web App"""
    has_topics_enabled: bool
    """:code:`True`, if the bot has forum topic mode enabled in private chats"""
    allows_users_to_create_topics: bool
    """:code:`True`, if the bot allows users to create and delete topics in private chats"""
    has_topic_sidebar: bool
    """:code:`True`, if topics in private chats with the bot are shown in a sidebar"""
    can_manage_bots: bool
    """:code:`True`, if other bots can be created to be controlled by the bot"""
    supports_join_request_queries: bool
    """:code:`True`, if the bot supports join request queries and can be assigned to process them"""
    username: str | None = None
    """*Optional*. Bot's username"""
    active_usernames: list[str] | None = None
    """*Optional*. If non-empty, the list of all `active usernames <https://telegram.org/blog/topics-in-groups-collectible-usernames#collectible-usernames>`_ of the bot"""
    inline_query_placeholder: str | None = None
    """*Optional*. Placeholder for inline queries, which is shown in the input field after the bot's username; omitted if the default placeholder is used"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: int,
            is_bot: bool,
            first_name: str,
            can_join_groups: bool,
            can_read_all_group_messages: bool,
            supports_guest_queries: bool,
            supports_inline_queries: bool,
            needs_inline_query_location: bool,
            can_connect_to_business: bool,
            has_main_web_app: bool,
            has_topics_enabled: bool,
            allows_users_to_create_topics: bool,
            has_topic_sidebar: bool,
            can_manage_bots: bool,
            supports_join_request_queries: bool,
            username: str | None = None,
            active_usernames: list[str] | None = None,
            inline_query_placeholder: str | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                id=id,
                is_bot=is_bot,
                first_name=first_name,
                can_join_groups=can_join_groups,
                can_read_all_group_messages=can_read_all_group_messages,
                supports_guest_queries=supports_guest_queries,
                supports_inline_queries=supports_inline_queries,
                needs_inline_query_location=needs_inline_query_location,
                can_connect_to_business=can_connect_to_business,
                has_main_web_app=has_main_web_app,
                has_topics_enabled=has_topics_enabled,
                allows_users_to_create_topics=allows_users_to_create_topics,
                has_topic_sidebar=has_topic_sidebar,
                can_manage_bots=can_manage_bots,
                supports_join_request_queries=supports_join_request_queries,
                username=username,
                active_usernames=active_usernames,
                inline_query_placeholder=inline_query_placeholder,
                **__pydantic_kwargs,
            )
