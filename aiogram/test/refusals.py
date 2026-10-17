"""
Every refusal the toolkit emits, declared once.

The Bot API authors advise clients to rely on the error code rather
than on the description. The toolkit follows that contract. Every
refusal guarantees its ``error_code`` and the exception type
``aiogram`` raises for it. The description is best-effort, except for
the texts below that carry ``guaranteed=True``.

A text is **sourced** when the toolkit takes it from the Bot API
server or from TDLib, and ``origin`` says which. It is **best-effort**
when ``origin`` is ``None``: the wording is the toolkit's own
approximation of Telegram's and may change. A guaranteed text is
always sourced, and is one that bots realistically match on. Adding a
text to that set is a promise, so a text without a citation cannot
join it.

A refusal site raises ``REFUSAL(**fields)``, never an
:class:`~aiogram.test.ApiRejection` built from a literal; a test
walks the sources to keep it that way.
"""

from __future__ import annotations

import dataclasses
import re
import string
from http import HTTPStatus

from aiogram.exceptions import TelegramAPIError

from .errors import _ERROR_PREFIXES, ApiRejection

__all__ = ("GUARANTEED", "REFUSALS", "Refusal", "refusal_of")

#: Where the Bot API server's own texts live.
_SERVER = "telegram-bot-api Client.cpp"
#: TDLib's, which the Bot API server relays.
_TDLIB = "TDLib"


@dataclasses.dataclass(frozen=True)
class Refusal:
    """
    One refusal: its text, its code and where the text comes from.

    ``text`` may hold ``{fields}`` that a raise site fills in.
    ``origin`` names the source of Telegram's wording, or is ``None``
    for the toolkit's approximation. ``guaranteed`` marks the texts
    a bot may match on.
    """

    text: str
    origin: str | None = None
    guaranteed: bool = False
    error_code: int = HTTPStatus.BAD_REQUEST

    def __post_init__(self) -> None:
        if self.guaranteed and self.origin is None:
            msg = f"{self.text!r} is guaranteed but cites no source"
            raise ValueError(msg)

    @property
    def sourced(self) -> bool:
        """Whether the wording comes from Telegram's own sources."""
        return self.origin is not None

    def format(self, **fields: object) -> str:
        """The description, with the raise site's fields filled in."""
        return self.text.format(**fields) if fields else self.text

    def __call__(
        self,
        *,
        retry_after: int | None = None,
        **fields: object,
    ) -> ApiRejection:
        """The :class:`ApiRejection` a raise site raises."""
        return ApiRejection(
            self.format(**fields),
            error_code=self.error_code,
            retry_after=retry_after,
            refusal=self,
        )


#: Every declared refusal, by its name in this module.
REFUSALS: dict[str, Refusal] = {}


def _declare(
    name: str,
    text: str,
    origin: str | None = None,
    *,
    guaranteed: bool = False,
    error_code: int = HTTPStatus.BAD_REQUEST,
) -> Refusal:
    refusal = Refusal(text, origin, guaranteed, error_code)
    REFUSALS[name] = refusal
    return refusal


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
REPLY_NOT_FOUND = _declare(
    "REPLY_NOT_FOUND",
    "message to be replied not found",
    _SERVER,
    guaranteed=True,
)
THREAD_NOT_FOUND = _declare(
    "THREAD_NOT_FOUND",
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
ENTITIES = _declare(
    "ENTITIES",
    "can't parse entities: {detail}",
    _TDLIB,
    guaranteed=True,
)

# -- sourced, not guaranteed ------------------------------------------

UNSUPPORTED_PARSE_MODE = _declare("UNSUPPORTED_PARSE_MODE", "unsupported parse_mode", _SERVER)
MESSAGE_TEXT_EMPTY = _declare("MESSAGE_TEXT_EMPTY", "message text is empty", _SERVER)
TEXT_MUST_BE_NON_EMPTY = _declare("TEXT_MUST_BE_NON_EMPTY", "text must be non-empty", _TDLIB)
FORWARD_NOT_FOUND = _declare("FORWARD_NOT_FOUND", "message to forward not found", _SERVER)
COPY_NOT_FOUND = _declare("COPY_NOT_FOUND", "message to copy not found", _SERVER)
PIN_NOT_FOUND = _declare("PIN_NOT_FOUND", "message to pin not found", _SERVER)
REACT_NOT_FOUND = _declare("REACT_NOT_FOUND", "message to react not found", _SERVER)
SUPERGROUPS_ONLY = _declare("SUPERGROUPS_ONLY", "method is available only in supergroups", _SERVER)
STICKER_SET_OCCUPIED = _declare(
    "STICKER_SET_OCCUPIED", "sticker set name is already occupied", _SERVER
)
CANT_BE_DELETED = _declare("CANT_BE_DELETED", "message can't be deleted", _SERVER)
SUPERGROUP_OR_CHANNEL_ONLY = _declare(
    "SUPERGROUP_OR_CHANNEL_ONLY",
    "method is available only in supergroup and channel chats",
    _SERVER,
)
CUSTOM_TITLE_RIGHTS = _declare(
    "CUSTOM_TITLE_RIGHTS",
    "not enough rights to change custom title of the user",
    _SERVER,
)
OWNER_PROTECTED = _declare("OWNER_PROTECTED", "can't remove chat owner", _TDLIB)
NOT_A_FORUM = _declare("NOT_A_FORUM", "the chat is not a forum", _TDLIB)
NOT_A_SUPERGROUP_FORUM = _declare(
    "NOT_A_SUPERGROUP_FORUM", "the chat is not a supergroup forum", _TDLIB
)
CHANNEL_POST_RIGHTS = _declare(
    "CHANNEL_POST_RIGHTS",
    "need administrator rights in the channel chat",
    _TDLIB,
)
SEND_RIGHTS = _declare("SEND_RIGHTS", "not enough rights to send {noun} to the chat", _TDLIB)
PIN_RIGHTS = _declare(
    "PIN_RIGHTS",
    "not enough rights to manage pinned messages in the chat",
    _TDLIB,
)
RESTRICT_RIGHTS = _declare(
    "RESTRICT_RIGHTS",
    "not enough rights to restrict/unrestrict chat member",
    _TDLIB,
)
PROMOTE_RIGHTS = _declare("PROMOTE_RIGHTS", "not enough rights", _TDLIB)
PERMISSIONS_RIGHTS = _declare(
    "PERMISSIONS_RIGHTS",
    "not enough rights to change chat permissions",
    _TDLIB,
)
STICKER_SET_RIGHTS = _declare(
    "STICKER_SET_RIGHTS",
    "not enough rights to change supergroup sticker set",
    _TDLIB,
)
SUGGESTED_POST_RIGHTS = _declare(
    "SUGGESTED_POST_RIGHTS", "message can't be used in the method", _TDLIB
)
INVITE_LINK_RIGHTS = _declare(
    "INVITE_LINK_RIGHTS",
    "not enough rights to manage chat invite link",
    _TDLIB,
)
JOIN_REQUEST_RIGHTS = _declare(
    "JOIN_REQUEST_RIGHTS",
    "not enough rights to manage chat join requests",
    _TDLIB,
)
CHAT_PHOTO_RIGHTS = _declare("CHAT_PHOTO_RIGHTS", "not enough rights to change chat photo", _TDLIB)
CHAT_TITLE_RIGHTS = _declare("CHAT_TITLE_RIGHTS", "not enough rights to change chat title", _TDLIB)
CHAT_DESCRIPTION_RIGHTS = _declare(
    "CHAT_DESCRIPTION_RIGHTS",
    "not enough rights to set chat description",
    _TDLIB,
)
CREATE_TOPIC_RIGHTS = _declare(
    "CREATE_TOPIC_RIGHTS", "not enough rights to create a topic", _TDLIB
)
EDIT_TOPIC_RIGHTS = _declare("EDIT_TOPIC_RIGHTS", "not enough rights to edit the topic", _TDLIB)
TOGGLE_TOPIC_RIGHTS = _declare(
    "TOGGLE_TOPIC_RIGHTS",
    "not enough rights to close or open the topic",
    _TDLIB,
)
DELETE_TOPIC_RIGHTS = _declare(
    "DELETE_TOPIC_RIGHTS", "not enough rights to delete the topic", _TDLIB
)

# -- best-effort: the toolkit's own approximation ---------------------

# The server answers these, and its texts are not in the open source.
CHAT_ADMIN_REQUIRED = _declare("CHAT_ADMIN_REQUIRED", "CHAT_ADMIN_REQUIRED")
TOPIC_CLOSED = _declare("TOPIC_CLOSED", "TOPIC_CLOSED")
TOPIC_DELETED = _declare("TOPIC_DELETED", "TOPIC_DELETED")
JOIN_REQUEST_NOT_PENDING = _declare(
    "JOIN_REQUEST_NOT_PENDING",
    "USER_ALREADY_PARTICIPANT: no join request is pending for this user",
)

# Wording the toolkit chose, as Telegram's is not known.
CANT_BE_EDITED = _declare("CANT_BE_EDITED", "message can't be edited")
CANT_BE_FORWARDED = _declare("CANT_BE_FORWARDED", "message can't be forwarded")
CANT_BE_COPIED = _declare("CANT_BE_COPIED", "message can't be copied")
READ_NOT_FOUND = _declare("READ_NOT_FOUND", "message to read not found")
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
ADMINISTRABLE_ONLY = _declare(
    "ADMINISTRABLE_ONLY",
    "method is available for supergroup and channel chats only",
)
ADMIN_RIGHTS_NOT_EDITABLE = _declare(
    "ADMIN_RIGHTS_NOT_EDITABLE",
    "not enough rights to change the administrator's rights",
)
NOT_AN_ADMINISTRATOR = _declare("NOT_AN_ADMINISTRATOR", "user is not an administrator")
NOT_A_REGULAR_MEMBER = _declare("NOT_A_REGULAR_MEMBER", "user is not a regular member")
NOT_A_CHAT_MEMBER = _declare("NOT_A_CHAT_MEMBER", "user is not a member of the chat")
STICKER_NOT_IN_SET = _declare("STICKER_NOT_IN_SET", "Sticker {file_id!r} is not in set {name!r}")
CHARGE_NOT_PAID_BY = _declare(
    "CHARGE_NOT_PAID_BY", "Charge {charge!r} was not paid by user {user_id}"
)
CHARGE_REFUNDED = _declare("CHARGE_REFUNDED", "Charge {charge!r} has already been refunded")
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
POLL_STOP_NOT_FOUND = _declare("POLL_STOP_NOT_FOUND", "message with poll to stop not found")
QUIZ_NEEDS_ANSWERS = _declare("QUIZ_NEEDS_ANSWERS", "a quiz poll must have correct_option_ids")
QUIZ_ANSWER_RANGE = _declare(
    "QUIZ_ANSWER_RANGE",
    "correct_option_ids {wrong} are not options of a {count}-option poll",
)
MESSAGE_MISSING = _declare(
    "MESSAGE_MISSING", "Message {message_id} does not exist in chat {chat_id}"
)
INVITE_LINK_MISSING = _declare(
    "INVITE_LINK_MISSING", "Invite link {url} does not exist in chat {chat_id}"
)
EPHEMERAL_REPLY_NEEDS_EPHEMERAL = _declare(
    "EPHEMERAL_REPLY_NEEDS_EPHEMERAL",
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
# The date and time entity's refusals: TDLib's texts for these are
# not known, so these are worded like its custom emoji ones.
ENTITIES_DATE_TIME = _declare("ENTITIES_DATE_TIME", "can't parse entities: {detail}")

#: The texts a bot may match on, as the documentation lists them.
GUARANTEED: tuple[Refusal, ...] = tuple(
    refusal for refusal in REFUSALS.values() if refusal.guaranteed
)


def _pattern(refusal: Refusal) -> re.Pattern[str]:
    parts = [
        re.escape(literal) + ("(?s:.*)" if field is not None else "")
        for literal, field, _, _ in string.Formatter().parse(refusal.text)
    ]
    return re.compile("".join(parts))


_PATTERNS = [(refusal, _pattern(refusal)) for refusal in REFUSALS.values()]


def refusal_of(error: TelegramAPIError | ApiRejection) -> Refusal | None:
    """
    The declared refusal an exception came from, if it names one.

    A test can tell two refusals of one error code apart without
    matching their best-effort wording: ``refusal_of(raised.value) is
    refusals.CANT_BE_DELETED``. It reads the description back against
    the declared texts, so it works on what a bot catches as well. Two
    refusals with the same text answer with the first one declared.
    """
    text = error.description if isinstance(error, ApiRejection) else error.message
    for prefix in _ERROR_PREFIXES.values():
        text = text.removeprefix(f"{prefix}: ")
    return next((r for r, pattern in _PATTERNS if pattern.fullmatch(text)), None)
