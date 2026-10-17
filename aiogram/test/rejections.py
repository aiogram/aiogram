"""
Every rejection the toolkit emits, declared once.

The Bot API authors advise clients to rely on the error code rather
than on the description. The toolkit follows that contract. Every
rejection guarantees its ``error_code`` and the exception type
``aiogram`` raises for it. The description is best-effort, except for
the ones below that carry ``guaranteed=True``.

A description is **sourced** when the toolkit takes it from the Bot
API server or from TDLib, and ``source`` says which. It is
**best-effort** when ``source`` is ``None``: the wording is the
toolkit's own approximation of Telegram's and may change. A guaranteed
description is always sourced, and is one that bots realistically
match on. Adding one to that set is a promise, so a description
without a citation cannot join it.

A site that refuses a call raises ``REJECTION(**fields)``, never an
:class:`~aiogram.test.ApiRejection` built from a literal; a test
walks the sources to keep it that way. No two descriptions may match
the same text, so :func:`rejection_of` can name the one that fired.
"""

from __future__ import annotations

import dataclasses
import re
import string
from http import HTTPStatus

from aiogram.exceptions import TelegramAPIError

from .errors import _ERROR_PREFIXES, ApiRejection

__all__ = (
    "ALL",
    "GUARANTEED",
    "Rejection",
    "rejection_fields",
    "rejection_of",
)

#: Where the Bot API server's own texts live.
_SERVER = "telegram-bot-api Client.cpp"
#: TDLib's, which the Bot API server relays.
_TDLIB = "TDLib"
#: MTProto errors, which the Bot API server passes through as the
#: description. Their text and meaning are in the method's error list.
_SEND_ERRORS = "Telegram API docs, messages.sendMessage errors"
_BAN_ERRORS = "Telegram API docs, messages.deleteChatUser errors"


@dataclasses.dataclass(frozen=True)
class Rejection:
    """
    One rejection: its description, its code and where it comes from.

    ``description`` may hold ``{fields}`` that a site fills in.
    ``source`` names where Telegram's wording comes from, or is
    ``None`` for the toolkit's approximation. ``guaranteed`` marks the
    descriptions a bot may match on.
    """

    description: str
    source: str | None = None
    guaranteed: bool = False
    error_code: int = HTTPStatus.BAD_REQUEST

    def __post_init__(self) -> None:
        if self.guaranteed and self.source is None:
            msg = f"{self.description!r} is guaranteed but cites no source"
            raise ValueError(msg)

    @property
    def sourced(self) -> bool:
        """Whether the wording comes from Telegram's own sources."""
        return self.source is not None

    def format(self, **fields: object) -> str:
        """The description, with the site's fields filled in."""
        return self.description.format(**fields) if fields else self.description

    def __call__(
        self,
        *,
        retry_after: int | None = None,
        **fields: object,
    ) -> ApiRejection:
        """The :class:`ApiRejection` a site raises."""
        return ApiRejection(
            self.format(**fields),
            error_code=self.error_code,
            retry_after=retry_after,
            rejection=self,
        )


#: Every declared rejection, by its name in this module.
ALL: dict[str, Rejection] = {}


def _declare(
    name: str,
    description: str,
    source: str | None = None,
    *,
    guaranteed: bool = False,
    error_code: int = HTTPStatus.BAD_REQUEST,
) -> Rejection:
    rejection = Rejection(description, source, guaranteed, error_code)
    ALL[name] = rejection
    return rejection


# -- the guaranteed texts ---------------------------------------------
# Sourced, and the ones a bot realistically matches on. The list the
# documentation prints is this one.

BOT_BLOCKED = _declare(
    "BOT_BLOCKED",
    "bot was blocked by the user",
    _SERVER,
    guaranteed=True,
    error_code=HTTPStatus.FORBIDDEN,
)
BOT_KICKED = _declare(
    "BOT_KICKED",
    "bot was kicked from the {noun} chat",
    _SERVER,
    guaranteed=True,
    error_code=HTTPStatus.FORBIDDEN,
)
BOT_NOT_A_MEMBER = _declare(
    "BOT_NOT_A_MEMBER",
    "bot is not a member of the {noun} chat",
    _SERVER,
    guaranteed=True,
    error_code=HTTPStatus.FORBIDDEN,
)
FLOOD = _declare(
    "FLOOD",
    "retry after {seconds}",
    _SERVER,
    guaranteed=True,
    error_code=HTTPStatus.TOO_MANY_REQUESTS,
)
MESSAGE_TO_EDIT_NOT_FOUND = _declare(
    "MESSAGE_TO_EDIT_NOT_FOUND",
    "message to edit not found",
    _SERVER,
    guaranteed=True,
)
MESSAGE_TO_DELETE_NOT_FOUND = _declare(
    "MESSAGE_TO_DELETE_NOT_FOUND",
    "message to delete not found",
    _SERVER,
    guaranteed=True,
)
MESSAGE_TO_BE_REPLIED_NOT_FOUND = _declare(
    "MESSAGE_TO_BE_REPLIED_NOT_FOUND",
    "message to be replied not found",
    _SERVER,
    guaranteed=True,
)
MESSAGE_THREAD_NOT_FOUND = _declare(
    "MESSAGE_THREAD_NOT_FOUND",
    "message thread not found",
    _SERVER,
    guaranteed=True,
)
QUERY_TOO_OLD = _declare(
    "QUERY_TOO_OLD",
    "query is too old and response timeout expired or query ID is invalid",
    _SERVER,
    guaranteed=True,
)
CANT_PARSE_ENTITIES = _declare(
    "CANT_PARSE_ENTITIES",
    "can't parse entities: {detail}",
    _TDLIB,
    guaranteed=True,
)

TOPIC_CLOSED = _declare("TOPIC_CLOSED", "TOPIC_CLOSED", _SEND_ERRORS, guaranteed=True)
TOPIC_DELETED = _declare("TOPIC_DELETED", "TOPIC_DELETED", _SEND_ERRORS, guaranteed=True)

# -- sourced, not guaranteed ------------------------------------------

CHAT_ADMIN_REQUIRED = _declare("CHAT_ADMIN_REQUIRED", "CHAT_ADMIN_REQUIRED", _BAN_ERRORS)
UNSUPPORTED_PARSE_MODE = _declare("UNSUPPORTED_PARSE_MODE", "unsupported parse_mode", _SERVER)
MESSAGE_TEXT_EMPTY = _declare("MESSAGE_TEXT_EMPTY", "message text is empty", _SERVER)
TEXT_MUST_BE_NON_EMPTY = _declare("TEXT_MUST_BE_NON_EMPTY", "text must be non-empty", _TDLIB)
MESSAGE_TO_FORWARD_NOT_FOUND = _declare(
    "MESSAGE_TO_FORWARD_NOT_FOUND", "message to forward not found", _SERVER
)
MESSAGE_TO_COPY_NOT_FOUND = _declare(
    "MESSAGE_TO_COPY_NOT_FOUND", "message to copy not found", _SERVER
)
MESSAGE_TO_PIN_NOT_FOUND = _declare(
    "MESSAGE_TO_PIN_NOT_FOUND", "message to pin not found", _SERVER
)
MESSAGE_TO_REACT_NOT_FOUND = _declare(
    "MESSAGE_TO_REACT_NOT_FOUND", "message to react not found", _SERVER
)
SUPERGROUPS_ONLY = _declare("SUPERGROUPS_ONLY", "method is available only in supergroups", _SERVER)
STICKER_SET_OCCUPIED = _declare(
    "STICKER_SET_OCCUPIED", "sticker set name is already occupied", _SERVER
)
MESSAGE_CANT_BE_DELETED = _declare("MESSAGE_CANT_BE_DELETED", "message can't be deleted", _SERVER)
SUPERGROUP_OR_CHANNEL_ONLY = _declare(
    "SUPERGROUP_OR_CHANNEL_ONLY",
    "method is available only in supergroup and channel chats",
    _SERVER,
)
NO_RIGHTS_TO_CHANGE_CUSTOM_TITLE = _declare(
    "NO_RIGHTS_TO_CHANGE_CUSTOM_TITLE",
    "not enough rights to change custom title of the user",
    _SERVER,
)
OWNER_PROTECTED = _declare("OWNER_PROTECTED", "can't remove chat owner", _TDLIB)
NOT_A_FORUM = _declare("NOT_A_FORUM", "the chat is not a forum", _TDLIB)
NOT_A_SUPERGROUP_FORUM = _declare(
    "NOT_A_SUPERGROUP_FORUM", "the chat is not a supergroup forum", _TDLIB
)
NO_RIGHTS_TO_POST_IN_CHANNEL = _declare(
    "NO_RIGHTS_TO_POST_IN_CHANNEL",
    "need administrator rights in the channel chat",
    _TDLIB,
)
NO_RIGHTS_TO_SEND = _declare(
    "NO_RIGHTS_TO_SEND", "not enough rights to send {noun} to the chat", _TDLIB
)
NO_RIGHTS_TO_PIN = _declare(
    "NO_RIGHTS_TO_PIN",
    "not enough rights to manage pinned messages in the chat",
    _TDLIB,
)
NO_RIGHTS_TO_RESTRICT = _declare(
    "NO_RIGHTS_TO_RESTRICT",
    "not enough rights to restrict/unrestrict chat member",
    _TDLIB,
)
NO_RIGHTS_TO_PROMOTE = _declare("NO_RIGHTS_TO_PROMOTE", "not enough rights", _TDLIB)
NO_RIGHTS_TO_CHANGE_PERMISSIONS = _declare(
    "NO_RIGHTS_TO_CHANGE_PERMISSIONS",
    "not enough rights to change chat permissions",
    _TDLIB,
)
NO_RIGHTS_TO_CHANGE_STICKER_SET = _declare(
    "NO_RIGHTS_TO_CHANGE_STICKER_SET",
    "not enough rights to change supergroup sticker set",
    _TDLIB,
)
SUGGESTED_POST_UNUSABLE = _declare(
    "SUGGESTED_POST_UNUSABLE", "message can't be used in the method", _TDLIB
)
NO_RIGHTS_TO_MANAGE_INVITE_LINKS = _declare(
    "NO_RIGHTS_TO_MANAGE_INVITE_LINKS",
    "not enough rights to manage chat invite link",
    _TDLIB,
)
NO_RIGHTS_TO_MANAGE_JOIN_REQUESTS = _declare(
    "NO_RIGHTS_TO_MANAGE_JOIN_REQUESTS",
    "not enough rights to manage chat join requests",
    _TDLIB,
)
NO_RIGHTS_TO_CHANGE_PHOTO = _declare(
    "NO_RIGHTS_TO_CHANGE_PHOTO", "not enough rights to change chat photo", _TDLIB
)
NO_RIGHTS_TO_CHANGE_TITLE = _declare(
    "NO_RIGHTS_TO_CHANGE_TITLE", "not enough rights to change chat title", _TDLIB
)
NO_RIGHTS_TO_CHANGE_DESCRIPTION = _declare(
    "NO_RIGHTS_TO_CHANGE_DESCRIPTION",
    "not enough rights to set chat description",
    _TDLIB,
)
NO_RIGHTS_TO_CREATE_TOPIC = _declare(
    "NO_RIGHTS_TO_CREATE_TOPIC", "not enough rights to create a topic", _TDLIB
)
NO_RIGHTS_TO_EDIT_TOPIC = _declare(
    "NO_RIGHTS_TO_EDIT_TOPIC", "not enough rights to edit the topic", _TDLIB
)
NO_RIGHTS_TO_TOGGLE_TOPIC = _declare(
    "NO_RIGHTS_TO_TOGGLE_TOPIC",
    "not enough rights to close or open the topic",
    _TDLIB,
)
NO_RIGHTS_TO_DELETE_TOPIC = _declare(
    "NO_RIGHTS_TO_DELETE_TOPIC", "not enough rights to delete the topic", _TDLIB
)

# -- best-effort: the toolkit's own approximation ---------------------

# The server answers this, and its text is not in the open source.
JOIN_REQUEST_NOT_PENDING = _declare(
    "JOIN_REQUEST_NOT_PENDING",
    "USER_ALREADY_PARTICIPANT: no join request is pending for this user",
)

# Wording the toolkit chose, as Telegram's is not known.
MESSAGE_CANT_BE_EDITED = _declare("MESSAGE_CANT_BE_EDITED", "message can't be edited")
MESSAGE_CANT_BE_FORWARDED = _declare("MESSAGE_CANT_BE_FORWARDED", "message can't be forwarded")
MESSAGE_CANT_BE_COPIED = _declare("MESSAGE_CANT_BE_COPIED", "message can't be copied")
MESSAGE_TO_READ_NOT_FOUND = _declare("MESSAGE_TO_READ_NOT_FOUND", "message to read not found")
NO_CONTENT_TO_EDIT = _declare("NO_CONTENT_TO_EDIT", "there is no {kind} in the message to edit")
ALBUM_ITEM_EDIT = _declare("ALBUM_ITEM_EDIT", "an album item can be edited only to {kinds}")
LIVE_PERIOD_RANGE = _declare(
    "LIVE_PERIOD_RANGE",
    "live_period must not exceed the current one by more than a day, and must end within 90 days",
)
MEDIA_GROUP_SIZE = _declare("MEDIA_GROUP_SIZE", "media group must include 2-10 items")
MEDIA_GROUP_MIXED = _declare(
    "MEDIA_GROUP_MIXED",
    "documents and audio files can be only grouped with messages of the same type",
)
MIXED_CHATS = _declare("MIXED_CHATS", "all messages must be from the same chat")
NO_PERSONAL_CHAT = _declare("NO_PERSONAL_CHAT", "user has no personal chat")
SUPERGROUP_OR_CHANNEL_ONLY = _declare(
    "SUPERGROUP_OR_CHANNEL_ONLY",
    "method is available for supergroup and channel chats only",
)
NO_RIGHTS_TO_EDIT_ADMINISTRATOR = _declare(
    "NO_RIGHTS_TO_EDIT_ADMINISTRATOR",
    "not enough rights to change the administrator's rights",
)
NOT_AN_ADMINISTRATOR = _declare("NOT_AN_ADMINISTRATOR", "user is not an administrator")
NOT_A_REGULAR_MEMBER = _declare("NOT_A_REGULAR_MEMBER", "user is not a regular member")
USER_NOT_A_MEMBER = _declare("USER_NOT_A_MEMBER", "user is not a member of the chat")
STICKER_NOT_IN_SET = _declare("STICKER_NOT_IN_SET", "Sticker '{file_id}' is not in set '{name}'")
CHARGE_NOT_PAID_BY = _declare(
    "CHARGE_NOT_PAID_BY", "Charge '{charge}' was not paid by user {user_id}"
)
CHARGE_REFUNDED = _declare("CHARGE_REFUNDED", "Charge '{charge}' has already been refunded")
GIFT_NEEDS_RECIPIENT = _declare("GIFT_NEEDS_RECIPIENT", "sendGift needs a user_id or a chat_id")
SUBSCRIPTION_PERIOD = _declare("SUBSCRIPTION_PERIOD", "subscription period must be {period}")
NOT_A_SUBSCRIPTION_LINK = _declare(
    "NOT_A_SUBSCRIPTION_LINK", "the link is not a subscription invite link"
)
POLL_PERIOD_CONFLICT = _declare(
    "POLL_PERIOD_CONFLICT", "open_period and close_date can't be used together"
)
POLL_SCHEDULE_RANGE = _declare(
    "POLL_SCHEDULE_RANGE",
    "a poll must close {shortest} to {longest} seconds from now",
)
NO_POLL = _declare("NO_POLL", "message doesn't contain a poll")
POLL_CLOSED = _declare("POLL_CLOSED", "poll has already been closed")
MESSAGE_WITH_POLL_TO_STOP_NOT_FOUND = _declare(
    "MESSAGE_WITH_POLL_TO_STOP_NOT_FOUND", "message with poll to stop not found"
)
QUIZ_NEEDS_ANSWERS = _declare("QUIZ_NEEDS_ANSWERS", "a quiz poll must have correct_option_ids")
QUIZ_ANSWER_RANGE = _declare(
    "QUIZ_ANSWER_RANGE",
    "correct_option_ids {wrong} are not options of a {count}-option poll",
)
MESSAGE_NOT_FOUND = _declare(
    "MESSAGE_NOT_FOUND", "Message {message_id} does not exist in chat {chat_id}"
)
INVITE_LINK_NOT_FOUND = _declare(
    "INVITE_LINK_NOT_FOUND", "Invite link {url} does not exist in chat {chat_id}"
)
REPLY_TO_EPHEMERAL_NOT_EPHEMERAL = _declare(
    "REPLY_TO_EPHEMERAL_NOT_EPHEMERAL",
    "a reply to an ephemeral message must itself be an ephemeral message",
)
EPHEMERAL_GROUPS_ONLY = _declare(
    "EPHEMERAL_GROUPS_ONLY",
    "ephemeral messages can be sent only to group and supergroup chats",
)
EPHEMERAL_REPLY_WINDOW = _declare(
    "EPHEMERAL_REPLY_WINDOW",
    "an ephemeral message can be replied to within 15 seconds only",
)
EPHEMERAL_CANT_REPLACE = _declare(
    "EPHEMERAL_CANT_REPLACE",
    "an ephemeral message can't replace an ephemeral message; "
    "edit it with the editEphemeralMessage methods instead",
)
REPLY_ELSEWHERE_UNSUPPORTED = _declare(
    "REPLY_ELSEWHERE_UNSUPPORTED",
    "a reply in another chat is not supported for ephemeral messages "
    "or messages sent on behalf of a business account",
)
# The date and time entity's rejections: TDLib's texts for these are
# not known, so these are worded like its custom emoji ones, under a
# prefix of their own so that no text is another's.
INVALID_DATE_TIME_ENTITY = _declare(
    "INVALID_DATE_TIME_ENTITY",
    "can't parse the date and time entity: {detail}",
)

#: The rejections a bot may match on, as the documentation lists them.
GUARANTEED: tuple[Rejection, ...] = tuple(
    rejection for rejection in ALL.values() if rejection.guaranteed
)


def _pattern(rejection: Rejection) -> re.Pattern[str]:
    parts = [
        re.escape(literal) + (f"(?P<{field}>.*?)" if field else "")
        for literal, field, _, _ in string.Formatter().parse(rejection.description)
    ]
    return re.compile("".join(parts), re.DOTALL)


_PATTERNS = {rejection: _pattern(rejection) for rejection in ALL.values()}

#: What aiogram puts before the description it was given.
_ORIGINAL = "\nOriginal description: "


def _description(error: TelegramAPIError | ApiRejection) -> str:
    if isinstance(error, ApiRejection):
        return error.description
    text = error.message.rpartition(_ORIGINAL)[2]
    for prefix in _ERROR_PREFIXES.values():
        text = text.removeprefix(f"{prefix}: ")
    return text


def _match(
    error: TelegramAPIError | ApiRejection,
) -> tuple[Rejection, re.Match[str]] | None:
    text = _description(error)
    if isinstance(error, ApiRejection):
        candidates = [] if error.rejection is None else [error.rejection]
    else:
        candidates = list(_PATTERNS)
    for rejection in candidates:
        if match := _PATTERNS[rejection].fullmatch(text):
            return rejection, match
    return None


def rejection_of(error: TelegramAPIError | ApiRejection) -> Rejection | None:
    """
    The declared rejection an exception came from, if it names one.

    A test can tell two rejections of one error code apart without
    matching their best-effort wording: ``rejection_of(raised.value)
    is rejections.MESSAGE_CANT_BE_DELETED``. An :class:`ApiRejection`
    answers with the one it was raised from. An exception a bot
    catches is read back against the declared descriptions, which
    also sees through the wording aiogram gives a flood or a migration.
    """
    found = _match(error)
    return None if found is None else found[0]


def rejection_fields(error: TelegramAPIError | ApiRejection) -> dict[str, str]:
    """
    The fields a rejection's description was filled in with.

    ``{"noun": "polls"}`` for a rejection to send polls. Empty when
    the exception names no rejection, or the rejection has no fields.
    """
    found = _match(error)
    return {} if found is None else found[1].groupdict()
