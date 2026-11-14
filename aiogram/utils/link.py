import warnings
from typing import Any
from urllib.parse import urlencode, urljoin

BASE_DOCS_URL = "https://docs.aiogram.dev/"
BRANCH = "dev-3.x"

BASE_PAGE_URL = f"{BASE_DOCS_URL}/en/{BRANCH}/"


def _format_url(url: str, *path: str, fragment_: str | None = None, **query: Any) -> str:
    url = urljoin(url, "/".join(path), allow_fragments=True)
    if query:
        url += "?" + urlencode(query)
    if fragment_:
        url += "#" + fragment_
    return url


def docs_url(*path: str, fragment_: str | None = None, **query: Any) -> str:
    return _format_url(BASE_PAGE_URL, *path, fragment_=fragment_, **query)


def create_tg_link(link: str, **kwargs: Any) -> str:
    return _format_url(f"tg://{link}", **kwargs)


def create_telegram_link(*path: str, **kwargs: Any) -> str:
    return _format_url("https://t.me", *path, **kwargs)


def create_channel_bot_link(
    username: str,
    parameter: str | None = None,
    change_info: bool = False,
    post_messages: bool = False,
    edit_messages: bool = False,
    delete_messages: bool = False,
    restrict_members: bool = False,
    invite_users: bool = False,
    pin_messages: bool = False,
    promote_members: bool = False,
    manage_video_chats: bool = False,
    anonymous: bool = False,
    manage_chat: bool = False,
    manage_topics: bool = False,
    post_stories: bool = False,
    edit_stories: bool = False,
    delete_stories: bool = False,
    manage_direct_messages: bool = False,
    manage_tags: bool = False,
) -> str:
    """
    Create a link that adds the bot to a channel as an administrator:
    :code:`https://t.me/<username>?startchannel&admin=<rights>`

    Source: https://core.telegram.org/api/links#group-channel-bot-links

    Telegram requires at least one administrator right for this flow;
    without any rights the plain bot link :code:`https://t.me/<username>` is returned.

    :param username: bot username
    :param parameter: deprecated, channel links have no start parameter;
        when passed, a group link :code:`?startgroup=<parameter>&admin=<rights>` is returned
    :return: link
    """
    rights = (
        ("change_info", change_info),
        ("post_messages", post_messages),
        ("edit_messages", edit_messages),
        ("delete_messages", delete_messages),
        ("restrict_members", restrict_members),
        ("invite_users", invite_users),
        ("pin_messages", pin_messages),
        ("manage_topics", manage_topics),
        ("promote_members", promote_members),
        ("manage_video_chats", manage_video_chats),
        ("anonymous", anonymous),
        ("manage_chat", manage_chat),
        ("post_stories", post_stories),
        ("edit_stories", edit_stories),
        ("delete_stories", delete_stories),
        ("manage_direct_messages", manage_direct_messages),
        ("manage_tags", manage_tags),
    )
    # The rights are joined with a literal "+", so they can't go through urlencode()
    admin = "+".join(name for name, enabled in rights if enabled)

    if parameter is not None:
        warnings.warn(
            "The 'parameter' argument of create_channel_bot_link() is deprecated: "
            "channel links have no start parameter, so a group link is created instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        link = create_telegram_link(username, startgroup=parameter)
        return f"{link}&admin={admin}" if admin else link

    if not admin:
        # ponytail: kept for backward compatibility, Telegram needs a right for ?startchannel
        return create_telegram_link(username)
    return f"{create_telegram_link(username)}?startchannel&admin={admin}"
