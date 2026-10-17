from __future__ import annotations

import dataclasses
import datetime
import re
from collections.abc import Callable, Iterable, Iterator
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, NamedTuple
from urllib.parse import parse_qs, urlsplit

from pydantic import BaseModel

from aiogram.enums import BotSubscriptionUpdatedState, ChatMemberStatus, ChatType
from aiogram.types import (
    BotSubscriptionUpdated,
    BusinessMessagesDeleted,
    CallbackQuery,
    ChatAdministratorRights,
    ChatBoostRemoved,
    ChatBoostUpdated,
    ChatJoinRequest,
    ChatMemberUpdated,
    ChosenInlineResult,
    CommunityChatAdded,
    CommunityChatRemoved,
    InlineKeyboardButton,
    InlineQuery,
    ManagedBotUpdated,
    Message,
    MessageGenerationStopped,
    MessageReactionCountUpdated,
    MessageReactionUpdated,
    PaidMediaPurchased,
    PollAnswer,
    PreCheckoutQuery,
    ReactionTypeEmoji,
    ReactionTypeUnion,
    RichMessageButton,
    ShippingQuery,
    SuccessfulPayment,
    Update,
    User,
)

from .markup import bot_command_entities
from .modeling import (
    SUBSCRIPTION_PERIOD,
    close_general,
    close_topic,
    delete_topic,
    edit_stamp,
    hide_general,
    holds_right,
    may_create_topics,
    reopen_general,
    reopen_topic,
    unhide_general,
)
from .mounting import owned_or_copied
from .synthesis import synthesize
from .world import (
    DEFAULT_TOPIC_ICON_COLOR,
    GROUP_ANONYMOUS_BOT_ID,
    BusinessConnectionState,
    ChargeState,
    ChatState,
    CommunityState,
    MemberState,
    PollState,
    QueryKind,
    TopicState,
    UserState,
    WorldLookupError,
    create_topic,
    group_anonymous_bot,
    mask,
    posted_by,
    resolve_topic,
)

if TYPE_CHECKING:
    from aiogram.client.bot import Bot
    from aiogram.fsm.context import FSMContext

    from .blueprint import BusinessConnectionSpec, ChatSpec, CommunitySpec, TopicSpec, UserSpec
    from .environment import BotTestEnvironment


class _DeepLink(NamedTuple):
    """A URL button parsed as a Telegram link, whatever kind of link it turns out to be."""

    username: str
    """
    The bot username the link addresses, empty for the kinds that address something else.

    Which kinds those are is `_LINK_KINDS[kind].match_by`, a property of the kind rather
    than of the individual link — a boost or video-chat link names a channel and a
    message link names its author, so neither can ever be "this bot", and
    `follow_deep_link` refuses them without comparing anything. The one kind whose
    username slot names something else *and* still concerns a bot is `attach`, where the
    bot is the payload instead; see `_addressed_bot`.
    """

    kind: str
    """A key of `_LINK_KINDS` — which of Telegram's documented link formats this url is."""

    payload: str
    """
    Whatever that kind carries: a `start` payload, a Mini App short name, an invite hash,
    the bot username of an `attach`, the raw query of an `unknown_query`. Read by the
    messages that interpolate it, and by `_addressed_bot` for the one kind that keeps its
    bot here.
    """


class _LinkKindPolicy(NamedTuple):
    """How a parsed link `kind` behaves in `follow_deep_link` and in `_parse_deep_link`."""

    followable: bool
    """Whether `follow_deep_link` can replay this kind as a `/start` — only `start`."""

    rejection: str
    """
    The message raised when this kind is used as an explicit target, or is the reason
    given when it is the only kind the automatic scan finds. A format string taking
    `url`, `kind` and `payload`; unused (left empty) for the one followable kind.
    """

    query_key: bool = False
    """
    Whether the kind's own name is a query parameter that selects it on a username link
    (`?startapp=`, `?boost`). Kinds Telegram spells differently in the query reach the
    same row through `_QUERY_KIND_ALIASES` instead.
    """

    match_by: str = ""
    """
    Which slot of the parsed link names the bot this link concerns, if any.

    ``"username"`` for every kind whose username slot is the bot's own
    (``t.me/<bot>?start=…``), ``"payload"`` for `attach`, where the username slot names
    the chat the attachment menu opens in and the bot is the parameter
    (``t.me/<chat>?attach=<bot>``), and empty for the kinds that concern no bot at all —
    a boost, an invite, a message link — which `follow_deep_link` refuses without
    comparing anything. `_parse_deep_link` keeps the parsed username only for the first,
    so a kind that matches on something else never carries a username to be mistaken for
    the bot's.
    """


_MATCH_USERNAME = "username"
_MATCH_PAYLOAD = "payload"


def _bot_link(
    reason: str,
    *,
    instead: str,
    query_key: bool = True,
    match_by: str = _MATCH_USERNAME,
) -> _LinkKindPolicy:
    """A link that concerns a bot, but is not the followable `start`."""
    return _LinkKindPolicy(
        followable=False,
        rejection=(
            f"{{url!r}} is a `{{kind}}` link, which {reason} in a real Telegram client; "
            f"only `start` deep links can be followed here — {instead}"
        ),
        query_key=query_key,
        match_by=match_by,
    )


def _foreign_link(reason: str, *, instead: str = "", query_key: bool = False) -> _LinkKindPolicy:
    """A documented Telegram link that addresses something other than a bot chat."""
    tail = f" — {instead}" if instead else ""
    return _LinkKindPolicy(
        followable=False,
        rejection=(
            f"{{url!r}} is {reason}, not a bot deep link; only "
            f"`t.me/<username>[?start=<payload>]` and "
            f"`tg://resolve?domain=<username>[&start=<payload>]` links can be followed "
            f"here{tail}"
        ),
        query_key=query_key,
    )


_MINI_APPS_NOT_SIMULATED = "Mini Apps run outside the update stream and are not simulated"

# Single source of truth for how each parsed `kind` behaves: whether `follow_deep_link`
# can replay it, the message when it can't, and the two structural facts
# `_parse_deep_link` needs — whether the kind is selected by a query parameter of its own
# name, and whether the parsed username means anything. Both derived tuples below come
# out of this table, and `follow_deep_link` and the automatic scan each do a single
# lookup here, so adding a kind Telegram documents later is a one-row change.
#
# The classification each row encodes follows https://core.telegram.org/api/links.
_LINK_KINDS: dict[str, _LinkKindPolicy] = {
    # -- links that address a bot by username ------------------------------------------
    "start": _LinkKindPolicy(
        followable=True,
        rejection="",
        query_key=True,
        match_by=_MATCH_USERNAME,
    ),
    "startgroup": _bot_link(
        "opens a group chooser, and the bot receives `/start@<bot> <payload>` in the "
        "group the user picks",
        instead="drive a group flow directly with `add_bot()` instead",
    ),
    "startchannel": _bot_link(
        "opens a channel chooser and adds the bot to the channel it picks",
        instead="drive a channel flow directly with `add_bot()` instead",
    ),
    "startapp": _bot_link("opens the bot's main Mini App", instead=_MINI_APPS_NOT_SIMULATED),
    "miniapp": _bot_link(
        "opens one of the bot's Mini Apps directly, by the short name in the path",
        instead=_MINI_APPS_NOT_SIMULATED,
        query_key=False,
    ),
    # `attach` is listed before `startattach` on purpose: the two co-occur in the form
    # Telegram documents for opening the menu in a specific chat
    # (`t.me/<chat>?attach=<bot>&startattach=<param>`), and there the `attach` reading is
    # the right one — `startattach` is only its parameter. `_QUERY_KIND_LOOKUP` derives
    # its order from this table, so the row order is where that precedence lives.
    "attach": _bot_link(
        "opens the attachment menu of @{payload} in the chat the link names",
        instead="the attachment menu is not simulated",
        # `t.me/<chat>?attach=<bot>` addresses the *chat* by username and names the bot in
        # the parameter, so the parameter is what tells whether the link is this bot's.
        match_by=_MATCH_PAYLOAD,
    ),
    "startattach": _bot_link(
        "installs the bot's attachment menu and opens it in the current chat",
        instead="the attachment menu is not simulated",
    ),
    "game": _bot_link(
        "opens a chat chooser to share the bot's `{payload}` game",
        instead="games are not simulated",
    ),
    "referral": _bot_link(
        "opens the bot through an affiliate program, crediting `{payload}`",
        instead="Telegram documents no `/start` for it, so use the "
        "`?start=<prefix><referrer>` form it documents alongside",
        query_key=False,
    ),
    "profile": _bot_link(
        "opens the profile page rather than the chat view",
        instead="nothing is sent from a profile page, so there is nothing to replay",
    ),
    "draft": _LinkKindPolicy(
        followable=False,
        rejection=(
            "{url!r} opens the chat with {payload!r} waiting as an unsent draft in a real "
            "Telegram client, so the bot receives nothing until the user presses send; "
            "only `start` deep links can be followed here — call `send({payload!r})` if "
            "the test needs that text delivered"
        ),
        match_by=_MATCH_USERNAME,
    ),
    "unknown_query": _LinkKindPolicy(
        followable=False,
        rejection=(
            "{url!r} carries a query Telegram does not define ({payload}); what a real "
            "Telegram client would do with it is not simulated — only "
            "`t.me/<username>[?start=<payload>]` and "
            "`tg://resolve?domain=<username>[&start=<payload>]` deep links can be "
            "followed here"
        ),
        match_by=_MATCH_USERNAME,
    ),
    # -- links that address a chat, a slug or the app itself ---------------------------
    "phone": _foreign_link(
        "a phone-number link (`t.me/+<digits>`), which opens a chat with whoever owns that number"
    ),
    "invite": _foreign_link(
        "a chat invite link (`t.me/+<hash>`), which offers to join a private chat"
    ),
    "joinchat": _foreign_link(
        "a legacy chat invite link (`t.me/joinchat/<hash>`), which offers to join a private chat"
    ),
    "message_link": _foreign_link(
        "a message link, which scrolls an existing chat to one of its messages"
    ),
    "story": _foreign_link(
        "a story link, which opens a story viewer",
        query_key=True,
    ),
    # Not in https://core.telegram.org/api/links — that page documents the links clients
    # must *handle*, and this one is served by t.me itself: `t.me/s/<username>` returns
    # the channel's posts as a web page. It is still a `t.me` link a bot can put on a
    # button, and it used to parse as `miniapp` of a bot called `s`, which is the one
    # thing it certainly is not.
    "channel_preview": _foreign_link(
        "a channel web-preview link (`t.me/s/<username>`), which opens a channel's posts "
        "as a web page rather than in a chat"
    ),
    "share": _foreign_link(
        "a share link, which opens a chat chooser with a draft the user still has to send"
    ),
    "invoice": _foreign_link(
        "an invoice link, which opens a payment form",
        instead="use `pay()` to complete a payment, or `pre_checkout_query()` for the "
        "step before it",
    ),
    "boost": _foreign_link(
        "a boost link, which opens the boost screen of a channel",
        instead="use `boost()` to deliver the `chat_boost` update instead",
        query_key=True,
    ),
    "videochat": _foreign_link(
        "a video-chat link, which offers to join a group call",
        query_key=True,
    ),
    "business": _foreign_link(
        "a business chat link (`t.me/m/<slug>`), which opens a chat with a business account"
    ),
    "stickerset": _foreign_link("a sticker- or emoji-set link, which offers to install a set"),
    "entity_ref": _foreign_link(
        "a `tg://user`-style entity reference, an internal Bot API abstraction for "
        "building message entities that clients never open as a link"
    ),
    "service_path": _foreign_link(
        "a Telegram service link (a proxy, theme, language pack, wallpaper, login code, "
        "chat folder or an app screen)"
    ),
    "extra_path": _foreign_link(
        "a `t.me` link whose extra path segments match none of Telegram's documented link formats"
    ),
}

# Query parameters Telegram spells differently from the kind they select, so `_LINK_KINDS`
# keeps one row per concept: the direct Mini App link's `tg://` form addresses the app by
# `appname`, `text` is a prefilled draft, `ref` an affiliate referrer, `voicechat` is the
# legacy spelling of `videochat`, `livestream` its channel form, and `post` is a message
# link's `tg://` form.
_QUERY_KIND_ALIASES: dict[str, str] = {
    "appname": "miniapp",
    "text": "draft",
    "ref": "referral",
    "livestream": "videochat",
    "voicechat": "videochat",
    "post": "message_link",
}

# Query parameters Telegram documents as *companions* of another link format as well as
# a format of their own: `startapp` is the Mini App start parameter carried by both
# `?startapp=` (the bot's main app) and `?appname=<short_name>` (a named one), and
# `startattach` the one carried by both `?startattach` (the current chat) and
# `?attach=<bot>` (a named chat), while `text` is the draft a public username link may
# carry alongside `?profile`. Each still names a kind when it arrives alone; it is simply
# the last thing consulted, so a query carrying one of these *and* the parameter that
# owns it is read as the owning format.
_COMPANION_QUERY_KEYS = frozenset({"startapp", "startattach", "text"})

# `(query key, kind)` pairs checked on a `t.me` / `tg://resolve` url, in the order they
# are looked for: everything else first, the companions above last. Order used to put the
# aliases first, which made `?startapp=x&text=y` a `draft` — refused as an unsent draft
# rather than as the Mini App a tapping user actually gets — while plain table order made
# `?appname=shop&startapp=ref` the bot's main app rather than the named one it opens.
# Within each half the table's own kinds come before the aliases, and `attach` sitting
# above `startattach` in the table is the one place that half's order decides anything.
#
# `start` is in neither half: it is not a plain lookup, because it only wins with a value
# — see `_parse_deep_link`.
_QUERY_KIND_LOOKUP: tuple[tuple[str, str], ...] = tuple(
    sorted(
        (
            *(
                (kind, kind)
                for kind, policy in _LINK_KINDS.items()
                if policy.query_key and kind != "start"
            ),
            *_QUERY_KIND_ALIASES.items(),
        ),
        key=lambda pair: pair[0] in _COMPANION_QUERY_KEYS,
    )
)

# First path segments `t.me` reserves, so they are never usernames. Everything Telegram
# documents but this toolkit sees no reason to tell apart shares a single honest
# `service_path` bucket; the rest get the kind their own row describes.
_RESERVED_PATH_KINDS: dict[str, str] = {
    "joinchat": "joinchat",
    "share": "share",
    "msg": "share",
    "invoice": "invoice",
    "boost": "boost",
    "addstickers": "stickerset",
    "addemoji": "stickerset",
    "m": "business",
    "c": "message_link",
    # `t.me/s/<username>`, the channel web preview. Reserved rather than parsed as a
    # username: `s` is a single letter, which Telegram's own username rules exclude.
    "s": "channel_preview",
    "addlist": "service_path",
    "addstyle": "service_path",
    "addtheme": "service_path",
    "auction": "service_path",
    "bg": "service_path",
    "call": "service_path",
    "confirmphone": "service_path",
    "contact": "service_path",
    "giftcode": "service_path",
    "login": "service_path",
    "newbot": "service_path",
    "nft": "service_path",
    "oauth": "service_path",
    "proxy": "service_path",
    "setlanguage": "service_path",
    "socks": "service_path",
}

# `tg://<host>` forms other than `tg://resolve`, which is the only one that addresses a
# bot. Anything else — `tg://settings`, `tg://proxy`, a host Telegram adds tomorrow — is
# an app screen, which is what the `service_path` fallback says.
_TG_HOST_KINDS: dict[str, str] = {
    "join": "invite",
    "msg_url": "share",
    "addstickers": "stickerset",
    "addemoji": "stickerset",
    "invoice": "invoice",
    "boost": "boost",
    "privatepost": "message_link",
    "message": "business",
    "user": "entity_ref",
    "emoji": "entity_ref",
    "time": "entity_ref",
}

_PHONE_NUMBER = re.compile(r"[0-9]+")
_APP_SHORT_NAME = re.compile(r"[A-Za-z0-9_]+")
# Bot API deep linking: "A-Z, a-z, 0-9, _ and - are allowed. ... up to 64 characters
# long" — https://core.telegram.org/bots/features#deep-linking.
_START_PAYLOAD = re.compile(r"[A-Za-z0-9_-]{1,64}")

#: Chat types Telegram delivers a `new_chat_members` service message in. A private chat
#: has no such concept — a bot starting a conversation is not "added" to it — and neither
#: does a channel, whose membership updates arrive only as `chat_member`/`my_chat_member`.
#: Only a plain group and a supergroup get the message a real client shows in the chat
#: itself, so `_change_membership`'s ``service_message`` only fires there.
_MEMBER_SERVICE_MESSAGE_CHAT_TYPES = frozenset({ChatType.GROUP, ChatType.SUPERGROUP})

#: The states ``BotSubscriptionUpdated.state`` can take.
_SUBSCRIPTION_STATES = frozenset(state.value for state in BotSubscriptionUpdatedState)


def _label(message: Message) -> str:
    """Name ``message`` in an error, by the id that finds it."""
    if message.ephemeral_message_id is not None:
        return f"Ephemeral message {message.ephemeral_message_id}"
    return f"Message {message.message_id}"


def _rejection_message(url: str, deep_link: _DeepLink) -> str:
    return _LINK_KINDS[deep_link.kind].rejection.format(
        url=url, kind=deep_link.kind, payload=deep_link.payload
    )


def _addressed_bot(deep_link: _DeepLink) -> str | None:
    """
    The bot username this link concerns, or `None` when it concerns no bot at all.

    The one lookup both `follow_deep_link` and the automatic scan use to ask "is this
    button about this bot?", so the two can never disagree. Which slot holds the answer
    is `_LINK_KINDS[kind].match_by`: usually the username the link addresses, but an
    attachment-menu link addresses the *chat* and names the bot in `?attach=`, and asking
    the username there produced both halves of the same bug — the scan skipped such a
    button as another chat's, and an explicit follow refused it as "not to this bot".
    """
    match_by = _LINK_KINDS[deep_link.kind].match_by
    if match_by == _MATCH_USERNAME:
        return deep_link.username
    if match_by == _MATCH_PAYLOAD:
        return deep_link.payload
    return None


def _path_deep_link(segments: list[str], query: dict[str, list[str]]) -> _DeepLink | None:
    """
    Classify a `t.me` path, or return `None` when the query is what decides the kind.

    The path shapes come from https://core.telegram.org/api/links: an invite hash or a
    phone number behind `+`, an invoice behind `$`, a reserved service segment, a story
    under `/s/`, a message by its numeric id, and a direct Mini App by its short name.
    The path decides first, with one documented exception the `query` is read for: see
    the phone branch.
    """
    first = segments[0]
    if first.startswith("+"):
        # `t.me/+<digits>` addresses a phone number and `t.me/+<hash>` a private chat;
        # an all-digit tail is exactly how Telegram's own clients tell the two apart.
        rest = first[1:]
        if _PHONE_NUMBER.fullmatch(rest):
            if "attach" in query:
                # `t.me/+<phone>?attach=<bot>` is the attachment-menu link documented
                # right beside `t.me/<username>?attach=<bot>`: the phone number is the
                # chat the menu opens in, so the link is about the bot in the query, and
                # calling it a phone link would hide that bot from the scan.
                return None
            return _DeepLink(username="", kind="phone", payload=rest)
        return _DeepLink(username="", kind="invite", payload=rest)
    if first.startswith("$"):
        return _DeepLink(username="", kind="invoice", payload=first[1:])
    reserved = _RESERVED_PATH_KINDS.get(first.lower())
    if reserved is not None:
        return _DeepLink(username="", kind=reserved, payload="/".join(segments[1:]))
    if len(segments) == 1:
        return None
    tail = segments[1:]
    if tail[0].lower() == "s":
        return _DeepLink(username="", kind="story", payload="/".join(tail[1:]))
    if all(segment.isdigit() for segment in tail):
        # `t.me/<username>/42` and the threaded `t.me/<username>/<thread>/42`.
        return _DeepLink(username="", kind="message_link", payload="/".join(tail))
    if len(tail) == 1 and _APP_SHORT_NAME.fullmatch(tail[0]):
        # `t.me/<bot>/<short_name>` — the one path form that does address a bot.
        return _DeepLink(username=first, kind="miniapp", payload=tail[0])
    return _DeepLink(username="", kind="extra_path", payload="/".join(tail))


def _require_valid_start_payload(url: str, payload: str) -> None:
    """
    Refuse a `start` payload Telegram would never have delivered.

    Bot API deep linking allows `A-Z`, `a-z`, `0-9`, `_` and `-`, up to 64 characters, so
    a real client tapping a button with an over-long, percent-encoded or non-Latin
    payload does not send `/start` with it — the link is simply broken. Handing the
    handler a payload production cannot produce would let a test pass on a bug in the
    button the bot built, so the toolkit names the rule instead.

    The Bot API states the rule but does not promise clients enforce it, and payloads
    that break it do reach production bots — which is what `follow_deep_link`'s
    ``validate_payload=False`` is for; this function is simply not called then.
    """
    if not payload or _START_PAYLOAD.fullmatch(payload):
        return
    msg = (
        f"{url!r} carries a `start` payload Telegram would not deliver ({payload!r}): a "
        f"start payload is 1-64 characters of `A-Z`, `a-z`, `0-9`, `_` and `-` "
        f"(https://core.telegram.org/bots/features#deep-linking), so a real client never "
        f"sends `/start` with it — fix the button's payload, or send the text yourself "
        f"with `send()`"
    )
    raise WorldLookupError(msg)


def _validate_rights(rights: dict[str, bool]) -> None:
    """
    Reject a right `ChatAdministratorRights` does not have, loudly and immediately.

    ``promote(**rights)`` opens the whole keyword space, and :func:`aiogram.test.world.mask`
    reads the fields it knows off the namespace and ignores everything else — so a
    misspelled right was accepted, silently dropped, and produced an administrator without
    it. The test then failed on the bot's "you are missing a right" branch, which is the
    correct behavior for the world it was actually given and says nothing about the typo.

    The shape deliberately mirrors :func:`aiogram.test.overrides._validated_fields`: the
    same failure — a keyword that can only ever be a mistake — reads the same way wherever
    the toolkit meets it.
    """
    known = ChatAdministratorRights.model_fields
    unknown = sorted(name for name in rights if name not in known)
    if unknown:
        listing = ", ".join(sorted(known))
        msg = (
            f"ChatAdministratorRights has no right(s) {', '.join(unknown)}, so promoting "
            f"with them would silently grant nothing.\n"
            f"  known rights: {listing}\n"
            f"Dispatcher data goes to `data={{...}}`, not into the rights."
        )
        raise TypeError(msg)


#: A button a user can press: one on an inline keyboard, or one inside a
#: message's rich content. Both carry ``callback_data`` and ``url``.
Button = InlineKeyboardButton | RichMessageButton


def _buttons_of(message: Message) -> Iterator[Button]:
    """
    Every button of a message, in the order a reader meets them.

    The inline keyboard comes first, then the rich content, depth-first
    in document order. The walk does not know which blocks hold buttons:
    rich text nests buttons through formatting, list items, details and
    table cells, and a block type a future Bot API version adds is
    walked the same way. It is iterative, so deep nesting cannot reach
    the recursion limit.
    """
    if message.reply_markup is not None:
        for row in message.reply_markup.inline_keyboard:
            yield from row
    stack: list[Any] = [message.rich_message]
    while stack:
        current = stack.pop()
        if isinstance(current, RichMessageButton):
            yield current
        elif isinstance(current, BaseModel):
            stack.extend(reversed(current.__dict__.values()))
        elif isinstance(current, list):
            stack.extend(reversed(current))


def _refuse_ephemeral(message: Message, action: str) -> None:
    """
    Refuse a user action on an ephemeral message.

    The Bot API does not describe a user editing or replying to one,
    so a test doing it would be guessing at behavior.
    """
    if message.ephemeral_message_id is not None:
        msg = (
            f"Ephemeral message {message.ephemeral_message_id} cannot be {action} by a "
            "user actor: the Bot API does not describe what that does"
        )
        raise WorldLookupError(msg)


#: The chats another bot's messages are checked for delivery in. A
#: private chat refuses them up front, and a channel post is the
#: channel's.
_GROUP_TYPES = frozenset({ChatType.GROUP, ChatType.SUPERGROUP})
_ADMINISTRATOR_STATUSES = frozenset({ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR})


@dataclasses.dataclass(frozen=True)
class Undelivered:
    """
    What a trigger returns when its update did not reach the bot.

    The world changed and stores what the trigger produced, exactly as
    when the update is delivered; only the dispatcher never saw
    ``update``. ``reason`` says why, in words: the test passed
    ``deliver=False``, or Telegram would not deliver it.
    """

    update: Update
    reason: str


def _detached(value: Any, bot: Bot) -> Any:
    """
    Copy what the caller handed a trigger, before an update carries it into the world.

    An update is mounted to the bot on the way in, and everything nested inside it is
    mounted with it — so a trigger that embeds the very object a test passed
    (``reaction=[HEART]``, ``fields={"reply_markup": MENU}``) binds that object to a bot,
    and a module-level constant stays bound for the rest of the session, no longer equal
    to the unbound copy the world keeps.

    Which is :func:`aiogram.test.mounting.owned_or_copied` exactly, with the copies left
    unbound: an update is mounted as a whole by
    :meth:`aiogram.test.BotTestEnvironment.feed`, so there is nothing here for binding them
    early to save. The world's own objects — a ``reply_to_message`` pointing back at a
    message the same actor sent earlier — pass through by identity, for the reasons stated
    there.
    """
    return owned_or_copied(value, owner=bot)


class UserActor:
    """
    A user, optionally bound to a chat, able to trigger updates.

    Every trigger builds a schema-valid :class:`~aiogram.types.Update` and feeds it to
    :meth:`aiogram.dispatcher.dispatcher.Dispatcher.feed_update`, so filters, middlewares,
    dependency injection and FSM all run exactly as they do in production. Keyword
    arguments are passed through as handler dependencies.

    Every trigger that feeds an update takes ``deliver``. With
    ``deliver=False`` the world changes and stores what the trigger
    produced, exactly as usual, and nothing is fed: the trigger
    returns :class:`Undelivered` instead of the handler's result. It
    reproduces an update Telegram never delivered, such as a lost
    ``forum_topic_closed``.
    """

    def __init__(
        self,
        environment: BotTestEnvironment,
        user: UserState,
        chat: ChatState | None = None,
        topic: TopicState | None = None,
        business: BusinessConnectionState | None = None,
        anonymous: bool = False,
    ) -> None:
        self.environment = environment
        self.user = user
        self._chat = chat
        self.topic = topic
        self.business = business
        #: Whether this actor posts as its supergroup, as an
        #: anonymous administrator does.
        self.anonymous = anonymous

    def in_(
        self,
        chat: ChatSpec | ChatState | int,
        *,
        topic: TopicSpec | TopicState | int | None = None,
        business: BusinessConnectionSpec | BusinessConnectionState | str | None = None,
        anonymous: bool = False,
    ) -> UserActor:
        """
        Bind this user to a chat, optionally to a topic or a business connection.

        Returns a new actor, leaving this one untouched. The binding decides what the
        triggers produce: a plain message, a topic-tagged message, or a business message.

        ``anonymous=True`` posts as the supergroup, as an anonymous
        administrator does: every message and service message is from
        ``GroupAnonymousBot``, with the group as ``sender_chat`` and the
        administrator's custom title as ``author_signature``. The user
        must be the owner or an administrator whose ``is_anonymous`` is
        set, or the binding raises :class:`WorldLookupError`. Rights
        are still the user's own.

        Binding to the actor's own id is the one case an undeclared chat is still
        allowed: every Telegram user *can* open a private chat with the bot, the same
        rule ``.chat`` applies to an unbound actor and a followed `/start` link opens on
        demand — see :meth:`~aiogram.test.world.World.ensure_private_chat`. Binding to
        any other undeclared chat id keeps raising: the world cannot invent a group's
        title, type or membership from a bare id.
        """
        if isinstance(chat, ChatState):
            state = chat
        else:
            chat_id = chat if isinstance(chat, int) else chat.id
            world = self.environment.world
            state = (
                world.ensure_private_chat(self.user)
                if chat_id == self.user.id
                else world.chat(chat_id)
            )
        if anonymous:
            self._require_anonymous(state)
        return UserActor(
            self.environment,
            self.user,
            state,
            topic=self._resolve_topic(state, topic),
            business=self.environment.business_connection(business) if business else None,
            anonymous=anonymous,
        )

    @staticmethod
    def _resolve_topic(
        chat: ChatState,
        topic: TopicSpec | TopicState | int | None,
    ) -> TopicState | None:
        if topic is None:
            return None
        return resolve_topic(chat, topic)

    def state(self) -> FSMContext:
        """
        FSM context for this actor's binding.

        The key is the one the dispatcher itself would use. An
        anonymous administrator's messages are from
        ``GroupAnonymousBot``, so its key is that user's, which every
        anonymous administrator of the chat shares.
        """
        return self.environment.state(
            GROUP_ANONYMOUS_BOT_ID if self.anonymous else self.user.id,
            self.chat.id,
            topic=self.topic,
            business_connection=self.business,
        )

    @property
    def chat(self) -> ChatState:
        """
        The chat this actor sends into — its own private chat when unbound.

        An unbound actor has no group or channel to guess at, but every Telegram user
        *can* open a private chat with the bot, so a plain `send()` opens it exactly like
        tapping a `/start` deep link does — see `World.ensure_private_chat`. `.in_(chat)`
        is still required for anywhere else: the world cannot invent a group's title,
        type or membership from a bare id.
        """
        if self._chat is not None:
            return self._chat
        return self.environment.world.ensure_private_chat(self.user)

    # -- triggers ---------------------------------------------------------------------

    async def send(
        self,
        text: str | None = None,
        *,
        fields: dict[str, Any] | None = None,
        reply_to: Message | int | None = None,
        ephemeral: bool = False,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        """
        Send a message as this user. ``fields`` overrides raw ``Message`` fields.

        ``reply_to`` is sugar for ``fields={"reply_to_message": ...}``: pass the
        `Message` itself, or the id of one already stored in `self.chat` — the id form
        resolves to the chat's own object rather than a copy, the same identity a
        hand-built ``reply_to_message`` gets by reaching into `self.chat.messages`
        directly. An explicit ``reply_to_message`` in ``fields`` still wins if both are
        given, matching every other field ``fields`` overrides.

        This trigger returns the handler's result, not the `Message` it sent — reach for
        ``self.chat.messages[-1]`` right after this call to get it, most of all when the
        next step is replying to it.

        ``ephemeral=True`` sends an ephemeral message, such as a
        command only the sender and the bot see. It has
        ``message_id`` 0 and an ``ephemeral_message_id``, stays out
        of the shared history, and is read back with
        ``self.chat.ephemeral_commands(user)``. Telegram has them in
        groups and supergroups only. An ``ephemeral_message_id`` in
        ``fields`` sends one the same way.
        """
        if ephemeral or (fields or {}).get("ephemeral_message_id") is not None:
            return await self._send_ephemeral(text, fields, reply_to, data, deliver=deliver)
        message = self._build_message(text=text, fields=self._with_reply_to(fields, reply_to))
        self.chat.add_message(message)
        if self.business is not None:
            return await self._feed(
                Update(update_id=self._next_update_id(), business_message=message),
                data,
                deliver=deliver,
            )
        update_id = self._next_update_id()
        if self.chat.type == ChatType.CHANNEL:
            return await self._feed(
                Update(update_id=update_id, channel_post=message), data, deliver=deliver
            )
        return await self._feed(
            Update(update_id=update_id, message=message), data, deliver=deliver
        )

    async def _send_ephemeral(
        self,
        text: str | None,
        fields: dict[str, Any] | None,
        reply_to: Message | int | None,
        data: dict[str, Any],
        deliver: bool = True,
    ) -> Any:
        chat = self.chat
        if chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
            msg = (
                f"Ephemeral messages exist in groups and supergroups only, and chat "
                f"{chat.id} is a {chat.type}; bind the actor with `.in_(group)`"
            )
            raise WorldLookupError(msg)
        if self.business is not None:
            msg = "A business connection does not carry ephemeral messages"
            raise WorldLookupError(msg)
        # Check the reply first, so a refused one uses up no id.
        requested = self._with_reply_to(fields, reply_to) or {}
        overrides = {"message_id": 0, **requested}
        ephemeral_id = overrides.get("ephemeral_message_id")
        if ephemeral_id is None:
            overrides["ephemeral_message_id"] = chat.allocate_ephemeral_message_id()
        elif chat.find_any_ephemeral(ephemeral_id) is not None:
            # Refused before anything is stored, so the chat is left
            # without a second message under the same id.
            msg = (
                f"Chat {chat.id} already holds an ephemeral message under ephemeral id "
                f"{ephemeral_id}; leave ephemeral_message_id out to have one allocated"
            )
            raise WorldLookupError(msg)
        message = self._build_message(text=text, fields=overrides)
        chat.add_ephemeral_command(message)
        return await self._feed(
            Update(update_id=self._next_update_id(), message=message),
            data,
            deliver=deliver,
        )

    async def reply(
        self,
        message: Message | int,
        text: str | None = None,
        *,
        fields: dict[str, Any] | None = None,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        """
        Reply to a message, as this user — sugar over ``send(reply_to=message, ...)``.

        ``message`` is the `Message` to reply to, or the id of one already stored in
        `self.chat`. Chaining a further reply onto this one reaches for
        ``self.chat.messages[-1]``, the reply this call just stored::

            await alice.reply(question, "42")
            await bob.reply(alice.chat.messages[-1], "same here")
        """
        return await self.send(text, fields=fields, reply_to=message, **data)

    async def edit(
        self,
        message: Message,
        text: str | None = None,
        *,
        fields: dict[str, Any] | None = None,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        """
        Edit a message this user sent earlier.

        Only what is passed changes: ``text`` when given, and the raw
        ``Message`` fields in ``fields``. The edit is dated with the
        world's clock through ``edit_date``, unless ``fields`` sets it.

        A user can edit only their own messages, so a message the
        actor did not send is refused. A channel post is attributed to
        the channel rather than to whoever published it, so an actor
        bound to a channel can edit the channel's posts. A forward
        shows another message's content, so no one can edit it.
        """
        _refuse_ephemeral(message, "edited")
        self._require_in_chat(message)
        stored = self._require_message(message.message_id)
        self._require_own(stored)
        if stored.forward_origin is not None:
            msg = (
                f"Message {stored.message_id} in chat {self.chat.id} is a forward, and "
                "a forward cannot be edited"
            )
            raise WorldLookupError(msg)
        changes: dict[str, Any] = edit_stamp(self.environment)
        if text is not None:
            changes["text"] = text
            if "entities" not in (fields or {}):
                # The commands of the new text replace those of the old.
                changes["entities"] = bot_command_entities(text) or None
        changes.update(_detached(fields or {}, self.environment.bot))
        edited = self.chat.update_message(message.message_id, **changes)
        if self.business is not None:
            return await self._feed(
                Update(update_id=self._next_update_id(), edited_business_message=edited),
                data,
                deliver=deliver,
            )
        update_id = self._next_update_id()
        if self.chat.type == ChatType.CHANNEL:
            return await self._feed(
                Update(update_id=update_id, edited_channel_post=edited),
                data,
                deliver=deliver,
            )
        return await self._feed(
            Update(update_id=update_id, edited_message=edited), data, deliver=deliver
        )

    async def click(
        self,
        target: str | Button,
        *,
        message: Message | None = None,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        """
        Press a button of a message the bot actually sent.

        ``target`` is the button's ``callback_data`` or the button
        itself, from an inline keyboard or from rich content.

        ``message`` names the message to press it on. It is looked up
        again in this actor's chat, by id or, for an ephemeral message
        addressed to the actor, by ephemeral id. The button must be on
        the stored version, which is the one the update carries, so a
        copy the bot has edited since cannot press a button that is
        gone.
        """
        callback_data = (
            target.callback_data
            if isinstance(target, (InlineKeyboardButton, RichMessageButton))
            else target
        )
        if callback_data is None:
            msg = "The button carries no callback_data and cannot be clicked"
            raise WorldLookupError(msg)
        if message is not None:
            self._require_visible(
                message,
                f"press callback_data={callback_data!r}",
                callback_data,
            )
            source = self._stored_button_message(message, callback_data)
        else:
            source = self._find_button_message(callback_data)
        world = self.environment.world
        query = CallbackQuery(
            id=world.next_query_id(QueryKind.CALLBACK),
            from_user=self.user.as_user(),
            chat_instance=str(self.chat.id),
            message=source,
            data=callback_data,
        )
        if source.ephemeral_message_id is not None:
            world.ephemeral_callbacks.add(query.id)
        return await self._feed(
            Update(update_id=self._next_update_id(), callback_query=query),
            data,
            deliver=deliver,
        )

    async def follow_deep_link(
        self,
        target: str | Button | None = None,
        *,
        message: Message | None = None,
        validate_payload: bool = True,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        """
        Follow a `t.me` deep-link button of a message the bot actually sent.

        Mirrors `click`'s validation guarantee — the button must really be there — but
        over `url` buttons that deep-link to this bot rather than `callback_data`
        buttons. Following the link is what a tapping user actually causes: their
        Telegram client opens a private chat with the bot and sends ``/start <payload>``
        there, so that is what this replays, through the same private-chat actor a test
        would build by hand.

        Only a ``start`` link is replayed that way. Every other format Telegram documents
        is refused with what a real client would have done with it instead — a Mini App
        launch opens an app, an invite link joins a chat, a share link only fills a draft
        — and so is a ``start`` link whose payload Telegram itself would not deliver; see
        `_parse_deep_link` and `_require_valid_start_payload`.

        Pass ``validate_payload=False`` to drop that last check and replay the payload
        exactly as the button carries it. The Bot API states the rule for what a bot
        should *put* in a link (1-64 characters of ``A-Za-z0-9_-``), but nothing enforces
        it on the way back, and production bots do receive payloads that break it —
        base64 padding (``=``), dots, more than 64 characters. Reproducing one of those
        in a test is what the escape hatch is for; the default stays strict, so a payload
        the bot itself built wrong is still named as the bug it is.
        """
        bot_username = self.bot_user.username or ""
        if isinstance(target, (InlineKeyboardButton, RichMessageButton)):
            url = target.url
            if url is None:
                msg = "The button carries no url and cannot be followed as a deep link"
                raise WorldLookupError(msg)
        else:
            url = target

        if message is not None:
            self._require_visible(message, "follow its deep-link buttons")
            # The link opens the private chat whichever chat showed
            # it, so the message is resolved in its own chat. A message
            # built by hand for a chat the world lacks is taken as is.
            shown_in = self.environment.world.chats.get(message.chat.id)
            if shown_in is not None:
                message = self._stored_version(message, shown_in)
        scope: Iterable[Message] = [message] if message is not None else self._visible_messages()
        deep_link: _DeepLink | None
        if url is None:
            url, deep_link = self._find_deep_link_url(scope, message, bot_username)
        else:
            self._require_button_url(scope, message, url)
            deep_link = self._parse_deep_link(url)

        if deep_link is None:
            msg = (
                f"{url!r} is not a Telegram deep-link url (expected a t.me link or a "
                f"tg://resolve link)"
            )
            raise WorldLookupError(msg)
        addressed = _addressed_bot(deep_link)
        if addressed is None:
            raise WorldLookupError(_rejection_message(url, deep_link))
        if addressed.lower() != bot_username.lower():
            msg = f"{url!r} deep-links to @{addressed}, not to this bot (@{bot_username})"
            raise WorldLookupError(msg)
        if not _LINK_KINDS[deep_link.kind].followable:
            raise WorldLookupError(_rejection_message(url, deep_link))
        if validate_payload:
            _require_valid_start_payload(url, deep_link.payload)

        text = f"/start {deep_link.payload}" if deep_link.payload else "/start"
        # Tapping the link is what opens the private chat — `UserActor.chat` now does
        # that for any unbound actor, the same as a plain `send()` from one, so this
        # just sends through a fresh actor for the same user rather than opening the
        # chat itself.
        return await UserActor(self.environment, self.user).send(text, deliver=deliver, **data)

    async def inline_query(
        self,
        query: str = "",
        *,
        offset: str = "",
        fields: dict[str, Any] | None = None,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        """
        Send an inline query, as this user, from the actor's chat.

        ``chat_type`` is ``sender`` from the actor's own private chat
        with the bot, which is where an unbound actor is, and the
        chat's type otherwise. ``fields`` overrides raw
        ``InlineQuery`` fields, such as ``location`` or a
        ``chat_type`` the binding cannot express.
        """
        bound = self._chat
        chat_type = "sender" if bound is None or bound.id == self.user.id else bound.type
        values: dict[str, Any] = {
            "id": self.environment.world.next_query_id(QueryKind.INLINE),
            "from_user": self.user.as_user(),
            "query": query,
            "offset": offset,
            "chat_type": chat_type,
        }
        values.update(_detached(fields or {}, self.environment.bot))
        inline = InlineQuery(**values)
        return await self._feed(
            Update(update_id=self._next_update_id(), inline_query=inline),
            data,
            deliver=deliver,
        )

    async def join(
        self, *, service_message: bool = True, deliver: bool = True, **data: Any
    ) -> Any:
        """
        Join this chat, producing `chat_member` — and, in a group, the
        `new_chat_members` service message a real join delivers alongside it.

        Pass ``service_message=False`` to get the old single-update behavior back.
        See :meth:`_change_membership` for why the group-only carve-out and the ordering
        between the two updates are what they are.

        A banned user cannot join, so it raises until the ban ends.
        """
        self._refuse_banned("join")
        return await self._change_membership(
            ChatMemberStatus.MEMBER, data, deliver=deliver, service_message=service_message
        )

    async def leave(self, *, deliver: bool = True, **data: Any) -> Any:
        """Leave this chat. A banned user is not in it, so it raises."""
        self._refuse_banned("leave")
        return await self._change_membership(ChatMemberStatus.LEFT, data, deliver=deliver)

    def _refuse_banned(self, action: str) -> None:
        """
        Refuse a move the user cannot make: only an unban ends a ban.

        Joining or leaving is the user's own, never the group's, so an
        actor bound anonymously cannot do it either.
        """
        if self.anonymous:
            msg = (
                f"An anonymous administrator cannot {action} chat {self.chat.id} as the "
                "group; bind the user without `anonymous=True`"
            )
            raise WorldLookupError(msg)
        if self.chat.member(self.user.id).status == ChatMemberStatus.KICKED:
            msg = (
                f"User {self.user.id} is banned from chat {self.chat.id}, so they cannot "
                f"{action} it; unban them first"
            )
            raise WorldLookupError(msg)

    async def add_bot(
        self, *, service_message: bool = True, deliver: bool = True, **data: Any
    ) -> Any:
        """
        Add the bot to this chat, producing `my_chat_member` rather than `chat_member` —
        and, in a group, the `new_chat_members` service message a real add delivers
        alongside it (see :meth:`_change_membership`).

        Pass ``service_message=False`` to get the old single-update behavior back.
        """
        return await self._change_membership(
            ChatMemberStatus.MEMBER,
            data,
            deliver=deliver,
            subject=self.bot_user,
            service_message=service_message,
        )

    async def remove_bot(self, *, deliver: bool = True, **data: Any) -> Any:
        return await self._change_membership(
            ChatMemberStatus.LEFT, data, deliver=deliver, subject=self.bot_user
        )

    async def promote(
        self,
        subject: UserSpec | UserState | int | None = None,
        *,
        data: dict[str, Any] | None = None,
        deliver: bool = True,
        **rights: bool,
    ) -> Any:
        """
        Promote a member to administrator, granting exactly the ``rights`` passed.

        ``subject`` names whose membership changes and defaults to the bot itself —
        promoting the bot is the one thing almost every group bot test needs before
        anything else works::

            await admin.in_(group).promote()  # the bot becomes an administrator

        Pass a `UserSpec`, a `UserState`, or a bare id to promote someone other than the
        bot — typically a third member, promoted by whoever ``self`` is.

        **A right this does not recognise is a typo, and is refused.** ``**rights`` is a
        wide-open keyword space and every name in it that is not a field of
        `ChatAdministratorRights` used to be dropped without a word — so
        ``promote(can_pin_message=True)`` produced an administrator who could not pin, and
        the test failed on the bot's "you are missing a right" branch with nothing to say
        which right or why. The names are checked against the model, exactly as
        `env.on(Method, field=...)` checks its filters, and a bad one names itself and the
        alternatives.

        ``data`` is the dispatcher data to feed the update with, spelled as a mapping
        because ``**kwargs`` here means rights. `demote` spells it the same way even though
        nothing competes for its keyword space, so the two twins take the same arguments —
        the asymmetry (one taking rights through ``**kwargs``, the other dispatcher data)
        was a trap worth removing rather than documenting::

            await admin.in_(group).promote(bob, can_pin_messages=True, data={"db": db})

        The rights are the *whole* mask, exactly like `promoteChatMember` itself (see
        :func:`aiogram.test.modeling.handle_promote`): a right this call does not name is
        denied, not inherited from an earlier promotion, so
        ``promote(can_pin_messages=True)`` is an administrator who can pin and nothing
        else. Unlike `promoteChatMember`, calling this with **no** rights at all still
        promotes rather than reading as a demotion — `promoteChatMember`'s "all `False`
        means demote" convention only makes sense when the caller is forced to state
        every field; here nothing stops a plain ``promote()``, and reading that as a
        demotion would make it silently do the opposite of what it says. Use `demote()`
        for that instead — it says what it means.

        Refuses to promote the chat's owner, exactly as `promoteChatMember` does: an
        owner's standing is not something even a fellow administrator can grant.
        """
        target = self._resolve_member_subject(subject)
        self._guard_not_owner(target)
        _validate_rights(rights)
        granted = mask(ChatAdministratorRights, SimpleNamespace(**rights), coerce=True)

        def _promote(member: MemberState) -> None:
            member.rights = ChatAdministratorRights(**granted)
            # The actor is now the promoter, so the bot may no longer
            # edit rights it granted before.
            member.promoted_by = self.user.id

        return await self._change_membership(
            ChatMemberStatus.ADMINISTRATOR,
            dict(data or {}),
            deliver=deliver,
            subject=target,
            mutate=_promote,
        )

    async def demote(
        self,
        subject: UserSpec | UserState | int | None = None,
        *,
        data: dict[str, Any] | None = None,
        deliver: bool = True,
    ) -> Any:
        """
        Demote an administrator back to a plain member.

        Mirrors what `promoteChatMember` does on a demotion (see
        :func:`aiogram.test.modeling.handle_promote`): the status drops to `MEMBER`, the
        rights are cleared, and so is the custom title — only an administrator or the
        owner carries one, so a title outliving the status is not something
        `getChatMember` could ever report. ``tag`` is untouched: it belongs to the
        membership itself, not to the administrator status, the same asymmetry
        `handle_promote` documents.

        ``subject`` defaults to the bot itself, the same as `promote()`. Refuses to
        demote the chat's owner, exactly as `promoteChatMember` does.

        Only an administrator can be demoted: a restricted, banned or
        absent user is refused, since demoting is not a way to lift a
        restriction or bring someone in.

        ``data`` is the dispatcher data to feed the update with, as a mapping rather than
        as ``**kwargs``. It used to be ``**data`` here and ``**rights`` on `promote`, so
        the same keyword on the two twins meant two different things — the one asymmetry in
        the trigger surface that could silently do the wrong thing. Both spell it ``data=``
        now; every other trigger, whose keyword space nothing competes for, keeps its
        ``**data``.
        """
        target = self._resolve_member_subject(subject)
        self._guard_not_owner(target)
        status = self.chat.member(target.id).status
        if status != ChatMemberStatus.ADMINISTRATOR:
            msg = (
                f"User {target.id} is {status} in chat {self.chat.id}, not an "
                "administrator, so there is nothing to demote"
            )
            raise WorldLookupError(msg)

        def _demote(member: MemberState) -> None:
            member.rights = None
            member.custom_title = None

        return await self._change_membership(
            ChatMemberStatus.MEMBER,
            dict(data or {}),
            deliver=deliver,
            subject=target,
            mutate=_demote,
        )

    async def enable_business_connection(self, *, deliver: bool = True, **data: Any) -> Any:
        return await self._business_connection_update(is_enabled=True, data=data, deliver=deliver)

    async def disable_business_connection(self, *, deliver: bool = True, **data: Any) -> Any:
        return await self._business_connection_update(is_enabled=False, data=data, deliver=deliver)

    async def delete_business_messages(
        self, message_ids: list[int], *, deliver: bool = True, **data: Any
    ) -> Any:
        """The business account deletes messages — they leave the chat, as in production."""
        connection = self._require_business()
        chat = self.chat
        for message_id in message_ids:
            if chat.find_message(message_id) is not None:
                chat.delete_message(message_id)
        event = BusinessMessagesDeleted(
            business_connection_id=connection.id,
            chat=chat.as_chat(),
            message_ids=message_ids,
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), deleted_business_messages=event),
            data,
            deliver=deliver,
        )

    async def set_topics(self, enabled: bool) -> None:
        """
        Turn the topics of this supergroup on or off, as its owner.

        Only the owner may, as TDLib checks, and only in a supergroup.
        Telegram delivers no update and no service message for it, so
        the bot learns of it from ``chat.is_forum`` on what comes next.

        Turning topics off keeps them, as a client does: turning them
        on again brings back every topic as it was. While they are off,
        a message the bot sends with a ``message_thread_id`` lands in
        the chat untagged, since the Bot API server passes no topic for
        a supergroup that is not a forum. Telegram does not document
        that, so it is an assumption read from the server's source.
        """
        chat = self.chat
        if chat.type != ChatType.SUPERGROUP:
            msg = (
                f"Topics can be turned on in supergroups only, and chat {chat.id} is a {chat.type}"
            )
            raise WorldLookupError(msg)
        if chat.member(self.user.id).status != ChatMemberStatus.CREATOR:
            msg = (
                f"Only the owner of chat {chat.id} can turn its topics on or off, and user "
                f"{self.user.id} is not; declare them with "
                f"`members={{user: ChatMemberStatus.CREATOR}}`"
            )
            raise WorldLookupError(msg)
        chat.is_forum = enabled

    async def create_topic(
        self,
        name: str,
        *,
        icon_color: int | None = None,
        icon_custom_emoji_id: str | None = None,
        deliver: bool = True,
        **data: Any,
    ) -> TopicState:
        """
        Create a topic in this forum, as a user who may manage topics.

        What :code:`createForumTopic` does for the bot, done by this
        user: the topic exists, and the ``forum_topic_created`` service
        message that opens it, from this user, is stored and fed to the
        dispatcher. It returns the new
        :class:`~aiogram.test.world.TopicState`, to bind an actor to or
        close later; the handler's result is not returned, and nor is
        :class:`Undelivered` when the message is withheld.

        The chat has to be a forum, and the user has to hold
        ``can_manage_topics``: as an administrator's right, or as the
        chat's permission of that name, which members have unless the
        chat or their restriction takes it away. Neither holding is
        something Telegram would let a client work around, so a test
        that lacks one has set the world up wrongly, and gets
        :class:`~aiogram.test.WorldLookupError`.
        """
        chat = self._require_topic_manager(creating=True)
        topic = create_topic(
            chat,
            name=name,
            date=self.environment.world.next_date(),
            icon_color=icon_color or DEFAULT_TOPIC_ICON_COLOR,
            icon_custom_emoji_id=icon_custom_emoji_id,
            from_user=self._sender(),
            creator_id=self._creator_id(),
            author_signature=self._signature(),
        )
        assert topic.root_message is not None
        await self._feed_message(topic.root_message, data, deliver=deliver)
        return topic

    async def close_topic(
        self,
        topic: TopicSpec | TopicState | int | None = None,
        *,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        """
        Close a topic, as a user who may manage topics.

        ``topic`` is the one to close and defaults to the topic this
        actor is bound to. The topic closes, and the
        ``forum_topic_closed`` service message, from this user, is
        stored and fed. See :meth:`create_topic` for who may and what
        happens when nobody does.
        """
        chat, target = self._managed_topic(topic, "close_general_topic")
        return await self._feed_message(
            close_topic(self.environment, chat, target, **self._service_sender()),
            data,
            deliver=deliver,
        )

    async def reopen_topic(
        self,
        topic: TopicSpec | TopicState | int | None = None,
        *,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        """Reopen a topic, feeding ``forum_topic_reopened``.

        See :meth:`close_topic`.
        """
        chat, target = self._managed_topic(topic, "reopen_general_topic")
        return await self._feed_message(
            reopen_topic(self.environment, chat, target, **self._service_sender()),
            data,
            deliver=deliver,
        )

    async def delete_topic(self, topic: TopicSpec | TopicState | int | None = None) -> None:
        """
        Delete a topic with all its messages, as a user who may manage
        topics.

        Telegram posts no service message for it and the Bot API has no
        type for one, so nothing is fed: the bot learns of it only when
        a call into the thread fails with ``message thread not found``.
        The General topic cannot be deleted.
        """
        chat, target = self._managed_topic(topic, None)
        delete_topic(chat, target)

    async def hide_general_topic(self, *, deliver: bool = True, **data: Any) -> Any:
        """
        Hide the General topic, which closes it, as a manager.

        The ``general_forum_topic_hidden`` service message, from this
        user, is stored and fed.
        """
        chat = self._require_topic_manager()
        return await self._feed_message(
            hide_general(self.environment, chat, **self._service_sender()), data, deliver=deliver
        )

    async def unhide_general_topic(self, *, deliver: bool = True, **data: Any) -> Any:
        """Unhide the General topic, feeding its service message."""
        chat = self._require_topic_manager()
        return await self._feed_message(
            unhide_general(self.environment, chat, **self._service_sender()),
            data,
            deliver=deliver,
        )

    async def close_general_topic(self, *, deliver: bool = True, **data: Any) -> Any:
        """
        Close the General topic, as a user who may manage topics.

        Like :code:`closeGeneralForumTopic`, it posts a
        ``forum_topic_closed`` message, from this user, which is stored
        and fed.
        """
        chat = self._require_topic_manager()
        return await self._feed_message(
            close_general(self.environment, chat, **self._service_sender()),
            data,
            deliver=deliver,
        )

    async def reopen_general_topic(self, *, deliver: bool = True, **data: Any) -> Any:
        """Reopen and unhide the General topic, feeding the message."""
        chat = self._require_topic_manager()
        return await self._feed_message(
            reopen_general(self.environment, chat, **self._service_sender()),
            data,
            deliver=deliver,
        )

    def _managed_topic(
        self,
        topic: TopicSpec | TopicState | int | None,
        general_trigger: str | None,
    ) -> tuple[ChatState, TopicState]:
        """The forum and the topic this actor closes or deletes."""
        self._require_topic_manager(opened=True)
        chat = self.chat
        target = self._require_regular_topic(chat, topic, general_trigger)
        if target.creator_id != self._creator_id():
            # The creator of a topic manages it without the right, as
            # TDLib's ``is_outgoing`` check lets it.
            self._require_topic_manager()
        return chat, target

    def _require_topic_manager(
        self,
        *,
        creating: bool = False,
        opened: bool = False,
    ) -> ChatState:
        """
        The forum this actor manages the topics of, or a setup error.

        ``creating`` asks whether the actor may open a topic, which a
        chat permission allows too; see :func:`may_create_topics`.
        ``opened`` checks only that the chat is a forum, for a topic
        the actor may have opened itself.
        """
        chat = self.chat
        if not chat.is_forum:
            msg = (
                f"Chat {chat.id} is not a forum, so it has no topics to manage; declare it "
                f"with `add_supergroup(..., is_forum=True)` or turn topics on with "
                f"`owner.set_topics(True)`"
            )
            raise WorldLookupError(msg)
        if opened:
            return chat
        allowed = (
            may_create_topics(chat, self.user.id)
            if creating
            else holds_right(chat, self.user.id, "can_manage_topics")
        )
        if not allowed:
            status = ChatMemberStatus(chat.member(self.user.id).status).value
            msg = (
                f"User {self.user.id} cannot manage the topics of chat {chat.id}: it takes "
                f"`can_manage_topics`, and their status is {status}. A trigger arranges the "
                f"world and does not refuse as Telegram would, so give them the right "
                f"with `blueprint.set_member(chat, user, rights=administrator_rights())`, "
                f"`members={{user: ChatMemberStatus.CREATOR}}`, or `promote(user, "
                f"can_manage_topics=True)`"
                + (", or grant it on the chat's `permissions`" if creating else "")
            )
            raise WorldLookupError(msg)
        return chat

    def _require_regular_topic(
        self,
        chat: ChatState,
        topic: TopicSpec | TopicState | int | None,
        general_trigger: str | None,
    ) -> TopicState:
        """The topic to act on: the one passed, else the bound one."""
        target = self.topic if topic is None else resolve_topic(chat, topic)
        if target is None:
            msg = (
                "No topic to act on: pass one, or bind this actor to one with "
                "`.in_(chat, topic=...)`"
            )
            raise WorldLookupError(msg)
        if target.is_general:
            via = f"; `{general_trigger}()` is the General topic's" if general_trigger else ""
            msg = f"The General topic of chat {chat.id} cannot be handled as a regular topic{via}"
            raise WorldLookupError(msg)
        return target

    async def _feed_message(
        self,
        message: Message,
        data: dict[str, Any],
        deliver: bool = True,
    ) -> Any:
        """Feed a service message already stored, from this chat."""
        return await self._feed(
            Update(update_id=self._next_update_id(), message=message),
            data,
            service=True,
            deliver=deliver,
        )

    async def add_chat_to_community(
        self,
        community: CommunitySpec | CommunityState | int,
        *,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        state = self.environment.community(community)
        chat = self.chat
        if chat.id not in state.chat_ids:
            state.chat_ids.append(chat.id)
        chat.community_id = state.id
        return await self._service_message(
            {"community_chat_added": CommunityChatAdded(community=state.as_community())},
            data,
            deliver=deliver,
        )

    async def remove_chat_from_community(
        self,
        community: CommunitySpec | CommunityState | int,
        *,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        state = self.environment.community(community)
        chat = self.chat
        if chat.id in state.chat_ids:
            state.chat_ids.remove(chat.id)
        chat.community_id = None
        return await self._service_message(
            {"community_chat_removed": CommunityChatRemoved()},
            data,
            deliver=deliver,
        )

    async def request_join(self, *, deliver: bool = True, **data: Any) -> Any:
        """
        Ask to join this chat, producing a `chat_join_request` the bot can act on.

        A banned user cannot ask to join, so it raises until the ban
        ends, as `join()` does.
        """
        self._refuse_banned("ask to join")
        chat = self.chat
        chat.join_requests.add(self.user.id)
        event = ChatJoinRequest(
            chat=chat.as_chat(),
            from_user=self.user.as_user(),
            user_chat_id=self.user.id,
            date=self.environment.world.next_date(),
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), chat_join_request=event),
            data,
            deliver=deliver,
        )

    async def chosen_inline_result(
        self,
        result_id: str,
        query: str = "",
        *,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        event = self._event(ChosenInlineResult, result_id=result_id, query=query)
        return await self._feed(
            Update(update_id=self._next_update_id(), chosen_inline_result=event),
            data,
            deliver=deliver,
        )

    async def shipping_query(
        self, invoice_payload: str = "payload", *, deliver: bool = True, **data: Any
    ) -> Any:
        event = self._event(
            ShippingQuery,
            id=self.environment.world.next_query_id(QueryKind.SHIPPING),
            invoice_payload=invoice_payload,
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), shipping_query=event),
            data,
            deliver=deliver,
        )

    async def pre_checkout_query(
        self,
        invoice_payload: str = "payload",
        *,
        currency: str = "XTR",
        total_amount: int = 1,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        event = self._event(
            PreCheckoutQuery,
            id=self.environment.world.next_query_id(QueryKind.PRE_CHECKOUT),
            invoice_payload=invoice_payload,
            currency=currency,
            total_amount=total_amount,
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), pre_checkout_query=event),
            data,
            deliver=deliver,
        )

    async def pay(
        self,
        invoice_payload: str = "payload",
        *,
        currency: str = "XTR",
        total_amount: int = 1,
        is_subscription: bool = False,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        """
        Complete a payment, posting the `successful_payment` message into the chat.

        The charge is recorded, so the handler can refund the id it was given rather than a
        fabricated one, and a star payment credits the bot's balance — see design decision
        D2 of `model-stars-and-gifts`.

        A subscription payment carries its expiration date, one
        subscription period from now, and ``is_first_recurring`` when
        it is this user's first subscription payment for
        ``invoice_payload``; a later one is a renewal.
        """
        world = self.environment.world
        renewal = is_subscription and any(
            charge.is_subscription
            and charge.user_id == self.user.id
            and charge.invoice_payload == invoice_payload
            for charge in world.stars.charges.values()
        )
        charge_id = f"charge-{world.next_query_id()}"
        world.stars.charges[charge_id] = ChargeState(
            id=charge_id,
            user_id=self.user.id,
            amount=total_amount,
            is_subscription=is_subscription,
            invoice_payload=invoice_payload,
        )
        if currency == "XTR":
            world.stars.record(
                world.next_query_id(),
                total_amount,
                world.next_date(),
                charge_id,
                partner_id=self.user.id,
            )
        subscription: dict[str, Any] = {
            "is_recurring": None,
            "is_first_recurring": None,
            "subscription_expiration_date": None,
        }
        if is_subscription:
            expires = world.next_date() + datetime.timedelta(seconds=SUBSCRIPTION_PERIOD)
            subscription = {
                "is_recurring": True,
                "is_first_recurring": None if renewal else True,
                "subscription_expiration_date": int(expires.timestamp()),
            }
        payment = self._event(
            SuccessfulPayment,
            invoice_payload=invoice_payload,
            currency=currency,
            total_amount=total_amount,
            telegram_payment_charge_id=charge_id,
            **subscription,
        )
        return await self._service_message({"successful_payment": payment}, data, deliver=deliver)

    async def purchase_paid_media(
        self, payload: str = "payload", *, deliver: bool = True, **data: Any
    ) -> Any:
        event = self._event(PaidMediaPurchased, paid_media_payload=payload)
        return await self._feed(
            Update(update_id=self._next_update_id(), purchased_paid_media=event),
            data,
            deliver=deliver,
        )

    async def boost(self, *, deliver: bool = True, **data: Any) -> Any:
        event = self._event(ChatBoostUpdated)
        return await self._feed(
            Update(update_id=self._next_update_id(), chat_boost=event),
            data,
            deliver=deliver,
        )

    async def remove_boost(self, *, deliver: bool = True, **data: Any) -> Any:
        event = self._event(ChatBoostRemoved)
        return await self._feed(
            Update(update_id=self._next_update_id(), removed_chat_boost=event),
            data,
            deliver=deliver,
        )

    async def stop_message_generation(
        self, draft_id: int = 1, *, deliver: bool = True, **data: Any
    ) -> Any:
        """
        The user taps the button that stops a draft's generation.

        Telegram shows that button only on a draft sent with
        ``can_stop=True`` (see
        :meth:`~aiogram.client.bot.Bot.send_message_draft`). Drafts are
        not tracked, so trigger this only where such a draft was sent.

        ``sendMessageDraft`` targets private chats, so the update is
        always about the user's own private chat with the bot, and the
        dispatcher resolves its user from that chat. An actor bound to
        any other chat raises instead. An actor bound to a topic of the
        private chat reports that topic's thread, as a message does.
        """
        chat = self.chat
        if chat.id != self.user.id:
            msg = (
                "stop_message_generation() happens only in the user's own private chat "
                "with the bot: sendMessageDraft targets private chats. Use the unbound "
                "actor, or bind it with `.in_(user)`"
            )
            raise WorldLookupError(msg)
        event = self._event(
            MessageGenerationStopped,
            draft_id=draft_id,
            message_thread_id=(
                self.topic.message_thread_id
                if self.topic is not None and not self.topic.is_general
                else None
            ),
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), stopped_message_generation=event),
            data,
            deliver=deliver,
        )

    async def guest_message(
        self,
        text: str | None = None,
        *,
        fields: dict[str, Any] | None = None,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        """
        A message from someone who is not a member, seen as a guest.

        It carries a ``guest_query_id``, unique in the world, which
        the bot answers with ``answerGuestQuery``. Answering is
        recorded, not modeled. ``fields`` overrides raw ``Message``
        fields.
        """
        overrides = {
            "guest_query_id": self.environment.world.next_query_id(),
            **(fields or {}),
        }
        message = self._build_message(text=text, fields=overrides)
        self.chat.add_message(message)
        return await self._feed(
            Update(update_id=self._next_update_id(), guest_message=message),
            data,
            deliver=deliver,
        )

    async def manage_bot(self, *, deliver: bool = True, **data: Any) -> Any:
        event = self._event(ManagedBotUpdated, user=self.user.as_user())
        # A synthesized user is not a bot, and the managed one is.
        event = event.model_copy(
            update={"bot_user": event.bot_user.model_copy(update={"is_bot": True})},
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), managed_bot=event),
            data,
            deliver=deliver,
        )

    async def update_subscription(
        self,
        invoice_payload: str = "payload",
        *,
        state: str = "active",
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        """
        The user's subscription to the bot changes ``state``.

        The Bot API names three states: ``canceled`` when the user
        cancels, ``active`` when they re-enable a cancelled
        subscription, and ``failed`` when a payment fails. Any other
        value is refused.
        """
        if state not in _SUBSCRIPTION_STATES:
            known = ", ".join(sorted(_SUBSCRIPTION_STATES))
            msg = f"A subscription state is one of {known}, not {state!r}"
            raise WorldLookupError(msg)
        event = self._event(
            BotSubscriptionUpdated,
            user=self.user.as_user(),
            invoice_payload=invoice_payload,
            state=state,
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), subscription=event),
            data,
            deliver=deliver,
        )

    async def vote(
        self, poll_id: str, options: list[int], *, deliver: bool = True, **data: Any
    ) -> Any:
        """
        Vote in a poll, producing `poll_answer` and recording the vote.

        An empty ``options`` retracts. Telegram never delivers an answer to a closed poll,
        so voting in one raises here — in the test's own code — rather than passing while
        asserting nothing (design decision D5).

        The answer must be one the poll accepts: options it has, one
        of them unless it allows multiple answers, and no change to an
        earlier vote unless it allows revoting. Retracting changes the
        vote, so it needs revoting too.
        """
        poll = self.environment.world.poll(poll_id)
        if poll.is_closed:
            msg = f"Poll {poll_id} is closed and cannot be voted in"
            raise WorldLookupError(msg)
        if poll.is_anonymous:
            msg = (
                f"Poll {poll_id} is anonymous, so Telegram never delivers a poll_answer "
                f"for it; use `poll_update()` to trigger the aggregate `poll` update"
            )
            raise WorldLookupError(msg)
        self._require_valid_vote(poll, options)
        if options:
            poll.votes[self.user.id] = list(options)
        else:
            poll.votes.pop(self.user.id, None)
        answer = PollAnswer(
            poll_id=poll_id,
            user=self.user.as_user(),
            option_ids=list(options),
            option_persistent_ids=[str(option) for option in options],
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), poll_answer=answer),
            data,
            deliver=deliver,
        )

    async def poll_update(self, poll_id: str, *, deliver: bool = True, **data: Any) -> Any:
        """The aggregate `poll` update, which is what an anonymous poll delivers."""
        poll = self.environment.world.poll(poll_id)
        return await self._feed(
            Update(update_id=self._next_update_id(), poll=poll.as_poll()),
            data,
            deliver=deliver,
        )

    async def react(
        self,
        message: Message | int,
        reaction: list[ReactionTypeUnion] | str | None = None,
        *,
        deliver: bool = True,
        **data: Any,
    ) -> Any:
        """
        React to a stored message, or remove this user's reaction with no ``reaction``.

        ``old_reaction`` is read before the mutation and ``new_reaction`` after, which is
        the only way those fields can be truthful (design decision D3).
        """
        chat = self.chat
        message_id = message if isinstance(message, int) else message.message_id
        if chat.find_message(message_id) is None:
            msg = f"Message {message_id} does not exist in chat {chat.id}"
            raise WorldLookupError(msg)
        if isinstance(reaction, str):
            new_reaction: list[ReactionTypeUnion] = [ReactionTypeEmoji(emoji=reaction)]
        else:
            new_reaction = _detached(reaction or [], self.environment.bot)
        # The stored reactions are copied out for the same reason the incoming ones are
        # copied in: the update binds whatever it carries, and the world's own objects are
        # compared against plainly declared ones.
        old = _detached(
            list(chat.reactions_for(message_id).get(self.user.id, [])), self.environment.bot
        )
        chat.set_reaction(message_id, self.user.id, new_reaction)
        event = MessageReactionUpdated(
            chat=chat.as_chat(),
            message_id=message_id,
            user=self.user.as_user(),
            date=self.environment.world.next_date(),
            old_reaction=old,
            new_reaction=new_reaction,
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), message_reaction=event),
            data,
            deliver=deliver,
        )

    async def reaction_count(
        self, message: Message | int, *, deliver: bool = True, **data: Any
    ) -> Any:
        """The aggregate reaction update, which is what an anonymous audience delivers."""
        chat = self.chat
        message_id = message if isinstance(message, int) else message.message_id
        event = MessageReactionCountUpdated(
            chat=chat.as_chat(),
            message_id=message_id,
            date=self.environment.world.next_date(),
            reactions=chat.reaction_counts(message_id),
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), message_reaction_count=event),
            data,
            deliver=deliver,
        )

    # -- internals --------------------------------------------------------------------

    def _event(self, event_type: type[Any], **overrides: Any) -> Any:
        """
        Synthesize an event, seeded from this actor's binding.

        The parts a test does not care about come from the same synthesizer the outbound
        side uses, so a Bot API change to any of these types needs no work here.
        """
        context = dataclasses.replace(
            self.environment.synthesis_context(),
            chat=self.chat.as_chat(),
            user=self.user.as_user(),
        )
        event = synthesize(event_type, context, name=event_type.__name__)
        return event.model_copy(update=overrides) if overrides else event

    def _require_valid_vote(self, poll: PollState, options: list[int]) -> None:
        """Refuse an answer Telegram would not deliver for ``poll``."""
        unknown = [option for option in options if not 0 <= option < len(poll.options)]
        if unknown:
            msg = (
                f"Poll {poll.id} has options 0-{len(poll.options) - 1}, so it has no "
                f"option(s) {unknown}"
            )
            raise WorldLookupError(msg)
        if len(options) > 1 and not poll.allows_multiple_answers:
            msg = (
                f"Poll {poll.id} does not allow multiple answers, so a vote for "
                f"{len(options)} options cannot be cast"
            )
            raise WorldLookupError(msg)
        previous = poll.votes.get(self.user.id)
        if (
            previous is not None
            and sorted(previous) != sorted(options)
            and not poll.allows_revoting
        ):
            msg = (
                f"Poll {poll.id} does not allow revoting, so user {self.user.id} "
                f"cannot change their vote {previous} to {list(options)}"
            )
            raise WorldLookupError(msg)

    def _require_business(self) -> BusinessConnectionState:
        if self.business is None:
            msg = (
                "This actor is not bound to a business connection; "
                "bind it with `.in_(chat, business=...)`"
            )
            raise WorldLookupError(msg)
        return self.business

    async def _business_connection_update(
        self,
        is_enabled: bool,
        data: dict[str, Any],
        deliver: bool = True,
    ) -> Any:
        connection = self._require_business()
        connection.is_enabled = is_enabled
        # The connection names the account owner whoever toggles it:
        # an actor bound to it may be a customer of that account.
        owner = self.environment.world.user(connection.user_id)
        event = connection.as_business_connection(owner.as_user())
        return await self._feed(
            Update(update_id=self._next_update_id(), business_connection=event),
            data,
            deliver=deliver,
        )

    async def _service_message(
        self,
        fields: dict[str, Any],
        data: dict[str, Any],
        deliver: bool = True,
    ) -> Any:
        message = self._build_message(text=None, fields=fields)
        self.chat.add_message(message)
        return await self._feed(
            Update(update_id=self._next_update_id(), message=message),
            data,
            service=True,
            deliver=deliver,
        )

    def _next_update_id(self) -> int:
        return self.environment.world.next_update_id()

    async def _feed(
        self,
        update: Update,
        data: dict[str, Any],
        *,
        service: bool = False,
        deliver: bool = True,
    ) -> Any:
        """
        Feed ``update``, unless it is withheld.

        ``deliver=False`` withholds it, and so does Telegram, for an
        update it would not deliver. ``service`` says the message it
        carries is a service message. What is withheld is still in the
        world, and the trigger returns :class:`Undelivered` instead of
        the handler's result.
        """
        if not deliver:
            return Undelivered(update, "withheld by the test with deliver=False")
        reason = self._withheld_by_telegram(update, service=service)
        if reason is not None:
            return Undelivered(update, reason)
        return await self.environment.feed(update, **data)

    def _is_other_bot(self) -> bool:
        """Whether this actor is a bot posting as itself."""
        return (
            self.user.is_bot
            and not self.anonymous
            and self.user.id != self.environment.world.bot_user.id
        )

    def _withheld_by_telegram(self, update: Update, *, service: bool) -> str | None:
        """
        Why Telegram would not deliver another bot's message, if not.

        A service message is delivered unless the environment
        withholds it; no public source says either way. A regular
        message in a group follows Bot-to-Bot Communication Mode, see
        :meth:`_reaches_bot`. Anything else is delivered.
        """
        message = update.message or update.edited_message
        if message is None or not self._is_other_bot():
            return None
        if service:
            if self.environment.deliver_bot_service_messages:
                return None
            return (
                f"a service message bot {self.user.id} caused, and the environment "
                "withholds those (deliver_bot_service_messages=False)"
            )
        if message.chat.type not in _GROUP_TYPES or self._reaches_bot(message):
            return None
        return (
            f"a message from bot {self.user.id}, which Telegram delivers to the bot only "
            "with Bot-to-Bot Communication Mode on one side and a mention or reply, or "
            "on the bot's side and the bot an administrator or out of privacy mode"
        )

    def _reaches_bot(self, message: Message) -> bool:
        """
        Whether another bot's group message reaches the bot.

        Telegram's rule (core.telegram.org/bots/features): with
        Bot-to-Bot Communication Mode on for either bot, a command
        naming the bot or a direct reply to it gets through; with it on
        for the bot, everything does while the bot is an administrator
        or has Group Privacy Mode off.
        """
        bot = self.environment.world.bot_user
        if (bot.bot_to_bot or self.user.bot_to_bot) and self._addresses_bot(message):
            return True
        if not bot.bot_to_bot:
            return False
        status = self.chat.member(bot.id).status
        return status in _ADMINISTRATOR_STATUSES or not self.environment.world.bot_privacy_mode

    def _addresses_bot(self, message: Message) -> bool:
        """
        Whether ``message`` names the bot in a command or replies to it.

        A topic's root, which every message in the topic replies to
        when it replies to nothing else, does not count: Telegram
        speaks of replying directly, and does not say whether an
        implicit reply does.
        """
        bot = self.environment.world.bot_user
        suffix = f"@{bot.username}".lower()
        for text, entities in (
            (message.text, message.entities),
            (message.caption, message.caption_entities),
        ):
            for entity in entities or []:
                if (
                    entity.type == "bot_command"
                    and text is not None
                    and entity.extract_from(text).lower().endswith(suffix)
                ):
                    return True
        reply = message.reply_to_message
        if reply is None or reply.from_user is None or reply.from_user.id != bot.id:
            return False
        return not (message.is_topic_message and reply.message_id == message.message_thread_id)

    def _require_anonymous(self, chat: ChatState) -> MemberState:
        """The membership that lets the user post as ``chat``."""
        if chat.type != ChatType.SUPERGROUP:
            msg = (
                f"Only a supergroup has anonymous administrators, and chat {chat.id} is a "
                f"{chat.type}"
            )
            raise WorldLookupError(msg)
        member = chat.member(self.user.id)
        rights = member.rights
        if (
            member.status not in _ADMINISTRATOR_STATUSES
            or rights is None
            or not rights.is_anonymous
        ):
            msg = (
                f"User {self.user.id} is not an anonymous administrator of chat {chat.id}, "
                f"so they cannot post as it; declare them with `blueprint.set_member(chat, "
                f"user, rights=administrator_rights(is_anonymous=True))` or "
                f"`promote(user, is_anonymous=True)`"
            )
            raise WorldLookupError(msg)
        return member

    def _sender(self) -> User:
        """Who this actor's messages are from."""
        return group_anonymous_bot() if self.anonymous else self.user.as_user()

    def _signature(self) -> str | None:
        """The custom title an anonymous administrator signs with."""
        if not self.anonymous:
            return None
        return self._require_anonymous(self.chat).custom_title

    def _service_sender(self) -> dict[str, Any]:
        """Who a service message this actor causes is from."""
        return {"by": self._sender(), "signature": self._signature()}

    def _creator_id(self) -> int:
        """
        Who a topic this actor opens counts as opened by.

        The group, for an anonymous administrator: TDLib keeps a
        topic's creator as a chat or a user. That the group is the
        creator here is an assumption.
        """
        return self.chat.id if self.anonymous else self.user.id

    def _build_message(self, text: str | None, fields: dict[str, Any] | None) -> Message:
        chat = self.chat
        bot = self.environment.world.bot_user
        if (
            chat.type == ChatType.PRIVATE
            and self._is_other_bot()
            and not (self.user.bot_to_bot and bot.bot_to_bot)
        ):
            msg = (
                f"Bot {self.user.id} cannot write to the bot in private: Telegram allows "
                "it only when both turn on Bot-to-Bot Communication Mode; declare "
                "`add_user(..., is_bot=True, bot_to_bot=True)` and "
                "`Blueprint(bot_to_bot=True)`"
            )
            raise WorldLookupError(msg)
        values: dict[str, Any] = {
            "date": self.environment.world.next_date(),
            "chat": chat.as_chat(),
            # A channel post is the channel's, whoever published it.
            **posted_by(chat, self._sender()),
        }
        signature = self._signature()
        if signature is not None:
            values["author_signature"] = signature
        if fields is None or "message_id" not in fields:
            values["message_id"] = chat.allocate_message_id(self.business)
        if chat.type == ChatType.CHANNEL:
            values["author_signature"] = self.user.first_name
        if text is not None:
            values["text"] = text
        if self.topic is not None:
            # A topic deleted since the actor was bound is no place to
            # post: this raises WorldLookupError naming it.
            resolve_topic(chat, self.topic)
        # With topics off, a client posts into the one flat chat.
        if self.topic is not None and not self.topic.is_general and chat.is_forum:
            values["message_thread_id"] = self.topic.message_thread_id
            values["is_topic_message"] = True
            # An explicit reply in `fields` replaces the root below.
            values.update(self.topic.root_reply({}))
        if self.business is not None:
            values["business_connection_id"] = self.business.id
        values.update(_detached(fields or {}, self.environment.bot))
        # A client marks the commands in a text, unless the test did.
        for text_field, entities_field in (("text", "entities"), ("caption", "caption_entities")):
            if entities_field not in (fields or {}):
                entities = bot_command_entities(values.get(text_field))
                if entities:
                    values[entities_field] = entities
        return Message(**values)

    def _with_reply_to(
        self,
        fields: dict[str, Any] | None,
        reply_to: Message | int | None,
    ) -> dict[str, Any] | None:
        """
        Fold ``reply_to`` into ``fields`` as ``reply_to_message``, ``fields`` winning.

        An int is resolved through `self.chat`, so the field carries the chat's own
        stored `Message` rather than a copy — the identity `_detached` (via
        :func:`aiogram.test.mounting.owned_or_copied`) already preserves for a
        ``reply_to_message`` a caller builds by hand from ``chat.messages``. Resolving it
        here rather than leaving the caller to look it up is the whole point of the
        keyword.

        A replied message that replies to something itself, such as a
        topic's root, is the one exception: a copy without its own
        ``reply_to_message``, since the Bot API never nests one, as the
        bot's sends store it.
        """
        if reply_to is None:
            return fields
        message = reply_to if isinstance(reply_to, Message) else self._require_message(reply_to)
        _refuse_ephemeral(message, "replied to")
        if message.reply_to_message is not None:
            message = message.model_copy(update={"reply_to_message": None})
        return {"reply_to_message": message, **(fields or {})}

    def _require_message(self, message_id: int) -> Message:
        message = self.chat.find_message(message_id)
        if message is None:
            msg = f"Message {message_id} does not exist in chat {self.chat.id}"
            raise WorldLookupError(msg)
        return message

    def _require_own(self, message: Message) -> None:
        """Refuse a user action on a message the user did not send."""
        sender = message.from_user
        if sender is not None and sender.id == self.user.id:
            return
        chat = self.chat
        sender_chat = message.sender_chat
        # A channel post is the channel's, whoever published it.
        if (
            chat.type == ChatType.CHANNEL
            and sender is None
            and sender_chat is not None
            and sender_chat.id == chat.id
        ):
            return
        # A message posted as the group is an anonymous actor's.
        if self.anonymous and sender_chat is not None and sender_chat.id == chat.id:
            return
        if sender is not None:
            author = f"user {sender.id}"
        elif sender_chat is not None:
            author = f"chat {sender_chat.id}"
        else:
            author = "no one"
        msg = (
            f"Message {message.message_id} in chat {chat.id} was sent by {author}, not by "
            f"user {self.user.id}, and a user can edit only their own messages"
        )
        raise WorldLookupError(msg)

    @staticmethod
    def _iter_buttons(scope: Iterable[Message]) -> Iterator[tuple[Message, Button]]:
        """Walk every button of every message, for every searcher."""
        for candidate in scope:
            for button in _buttons_of(candidate):
                yield candidate, button

    def _visible_messages(self) -> Iterator[Message]:
        """
        The messages this actor can press buttons on, newest first.

        Its own ephemeral messages come first: they are addressed to it,
        and with ``message_id`` 0 they cannot be ordered against the
        shared history by id.
        """
        yield from reversed(self.chat.ephemeral_messages(self.user.id))
        yield from reversed(self.chat.messages)

    def _require_visible(
        self,
        message: Message,
        action: str,
        callback_data: str | None = None,
    ) -> None:
        """Refuse acting on someone else's ephemeral message."""
        receiver = message.receiver_user
        if message.ephemeral_message_id is None or (
            receiver is not None and receiver.id == self.user.id
        ):
            return
        # The message names its own receiver: scanning for the button
        # could find another receiver's message with the same data.
        hint = ""
        if callback_data is not None and receiver is not None:
            hint = (
                f"; it is addressed to user {receiver.id} ({receiver.first_name!r}) "
                "— click as that user"
            )
        msg = (
            f"Ephemeral message {message.ephemeral_message_id} is not addressed to user "
            f"{self.user.id}, so they cannot {action} on it{hint}"
        )
        raise WorldLookupError(msg)

    def _require_in_chat(self, message: Message) -> None:
        """Refuse a message from a chat other than the actor's."""
        chat = self.chat
        if message.chat.id != chat.id:
            msg = (
                f"Message {message.message_id} is in chat {message.chat.id}, but this "
                f"actor is bound to chat {chat.id}; bind it with `.in_(...)`"
            )
            raise WorldLookupError(msg)

    def _stored_version(self, message: Message, chat: ChatState) -> Message:
        """
        The version of ``message`` that ``chat`` holds now.

        Telegram acts on a message as the chat holds it, so a copy the
        test kept is looked up again, by id or, for an ephemeral
        message addressed to the actor, by ephemeral id.
        """
        if message.ephemeral_message_id is not None:
            stored = chat.find_ephemeral_message(self.user.id, message.ephemeral_message_id)
        else:
            stored = chat.find_message(message.message_id)
        if stored is None:
            msg = f"{_label(message)} does not exist in chat {chat.id}"
            raise WorldLookupError(msg)
        return stored

    def _stored_button_message(self, message: Message, callback_data: str) -> Message:
        """The stored ``message``, which must carry the button."""

        def carries(candidate: Message) -> bool:
            return any(button.callback_data == callback_data for button in _buttons_of(candidate))

        self._require_in_chat(message)
        stored = self._stored_version(message, self.chat)
        if carries(stored):
            return stored
        msg = (
            f"{_label(message)} in chat {self.chat.id} carries no button with "
            f"callback_data={callback_data!r}"
        )
        if stored is not message and carries(message):
            msg += "; the copy passed does, but the message was edited since"
        raise WorldLookupError(msg)

    def _find_button_message(self, callback_data: str) -> Message:
        for candidate, button in self._iter_buttons(self._visible_messages()):
            if button.callback_data == callback_data:
                return candidate
        msg = (
            f"No message in chat {self.chat.id} carries a button with "
            f"callback_data={callback_data!r}{self._misdirected_callback_hint(callback_data)}"
        )
        raise WorldLookupError(msg)

    def _misdirected_callback_hint(self, callback_data: str) -> str:
        """
        Point at the chat a forgotten ``.in_(...)`` left the button behind in.

        A `click()` on an actor bound to the wrong chat and one on a button that never
        existed both fail with the same plain "no button here" message, and the two are
        easy to conflate — a test that meant ``admin.in_(group).click(...)`` but forgot
        the binding sees a message identical to a genuine typo in ``callback_data``. This
        scans the rest of the world for the button before giving up, so the first case
        says so directly instead of leaving the search to whoever reads the failure.
        """
        receiver = self._receiver_hint(callback_data)
        if receiver:
            return receiver
        this_chat_id = self.chat.id
        for chat_id, chat in self.environment.world.chats.items():
            if chat_id == this_chat_id:
                continue
            for _candidate, button in self._iter_buttons(reversed(chat.messages)):
                if button.callback_data == callback_data:
                    title = chat.title or chat.username or chat.first_name or str(chat_id)
                    return (
                        f"; a button with this callback_data exists in chat {chat_id} "
                        f"({title!r}) — bind the actor with `.in_(...)`"
                    )
        return ""

    def _receiver_hint(self, callback_data: str) -> str:
        """Name whom an ephemeral message with the button is for."""
        for receiver_id, messages in self.chat.sent_ephemeral.items():
            if receiver_id == self.user.id:
                continue
            for _candidate, button in self._iter_buttons(reversed(messages)):
                if button.callback_data == callback_data:
                    name = self.environment.world.user(receiver_id).first_name
                    return (
                        f"; a button with this callback_data is on an ephemeral message "
                        f"addressed to user {receiver_id} ({name!r}) — click as that user"
                    )
        return ""

    def _find_deep_link_url(
        self,
        scope: Iterable[Message],
        message: Message | None,
        bot_username: str,
    ) -> tuple[str, _DeepLink]:
        """
        Scan buttons front-to-back for the newest followable (`start`) link to this bot.

        A button that targets this bot with some other kind — a `startgroup` chooser, a
        Mini App, an attachment-menu launch — is never picked as if it were a plain
        `start` link; it is remembered as a candidate instead, so a keyboard mixing such
        a button with a real `start` link still finds the `start` link, and one that
        carries only unfollowable candidates says exactly why each was rejected.
        """
        candidates: list[tuple[str, _DeepLink]] = []
        for _candidate, button in self._iter_buttons(scope):
            if button.url is None:
                continue
            deep_link = self._parse_deep_link(button.url)
            if deep_link is None:
                continue
            addressed = _addressed_bot(deep_link)
            if addressed is None or addressed.lower() != bot_username.lower():
                continue
            if _LINK_KINDS[deep_link.kind].followable:
                return button.url, deep_link
            candidates.append((button.url, deep_link))
        if candidates:
            details = "; ".join(_rejection_message(url, dl) for url, dl in candidates)
            if message is not None:
                msg = (
                    f"{_label(message)} carries no followable (`start`) "
                    f"deep-link button to @{bot_username}, only unfollowable ones: {details}"
                )
            else:
                msg = (
                    f"No message in chat {self.chat.id} carries a followable (`start`) "
                    f"deep-link button to @{bot_username}, only unfollowable ones: {details}"
                )
            raise WorldLookupError(msg)
        if message is not None:
            msg = f"{_label(message)} carries no deep-link button to @{bot_username}"
        else:
            msg = (
                f"No message in chat {self.chat.id} carries a deep-link button to @{bot_username}"
            )
        raise WorldLookupError(msg)

    def _require_button_url(
        self,
        scope: Iterable[Message],
        message: Message | None,
        url: str,
    ) -> None:
        for _candidate, button in self._iter_buttons(scope):
            if button.url == url:
                return
        if message is not None:
            msg = f"Message {message.message_id} does not carry a button with url={url!r}"
        else:
            msg = f"No message in chat {self.chat.id} carries a button with url={url!r}"
        raise WorldLookupError(msg)

    @staticmethod
    def _parse_deep_link(url: str) -> _DeepLink | None:
        """
        Parse any Telegram link into the `kind` https://core.telegram.org/api/links gives it.

        Recognizes ``https://t.me/<username>[?start=<payload>]`` (also ``http://`` and
        schemeless ``t.me/...``) and ``tg://resolve?domain=<username>[&start=<payload>]``.
        A query with no ``start`` key at all — most of all no query, a bare profile link
        — parses as a plain start with no payload; a ``start`` *with a value* wins over
        every other parameter, harmless (``utm_source=...``) or not, including the
        start-ish ones (``?start=x&startapp=y`` is a followable start carrying ``x``),
        since a real Telegram client reads only the parameter it recognizes and ignores
        the rest of the query. An empty ``?start=`` carries no such reading: it wins over
        nothing, so ``?start=&startapp=y`` is the Mini App link it is, and ``?start=``
        alone is the bare ``/start`` that ``t.me/<bot>`` already is.

        Every other documented format is recognized too, and tagged with its own `kind`
        rather than silently downgraded to a plain start or lumped into one bucket: the
        path decides first (a phone number or an invite hash behind ``+``, an invoice
        behind ``$`` or under ``/invoice/``, a reserved segment such as ``/share`` or
        ``/addstickers``, a story under ``/s/``, a message by its numeric id, a direct
        Mini App by its short name — see `_path_deep_link`), then the query
        (`_QUERY_KIND_LOOKUP`), and a query carrying none of the parameters Telegram
        documents falls back to ``unknown_query``. A ``tg://`` url that is not
        ``tg://resolve`` is classified by its host (`_TG_HOST_KINDS`), down to a
        ``service_path`` fallback: those are app screens, but they are still Telegram
        links, and saying so beats claiming they are not.

        Returns ``None`` only for urls that are not Telegram links at all — another host,
        another scheme, a ``t.me`` url with no path, a ``tg://resolve`` naming neither a
        domain nor a phone.
        """
        candidate = url if "://" in url else f"https://{url}"
        parsed = urlsplit(candidate)
        scheme = parsed.scheme.lower()
        query = parse_qs(parsed.query, keep_blank_values=True)
        if scheme in {"http", "https"}:
            if parsed.netloc.lower() not in {"t.me", "telegram.me"}:
                return None
            segments = [segment for segment in parsed.path.split("/") if segment]
            if not segments:
                return None
            by_path = _path_deep_link(segments, query)
            if by_path is not None:
                return by_path
            username = segments[0]
        elif scheme == "tg":
            host = parsed.netloc.lower()
            if host != "resolve":
                kind = _TG_HOST_KINDS.get(host, "service_path")
                return _DeepLink(username="", kind=kind, payload=parsed.query)
            phones = query.get("phone")
            if phones and phones[0]:
                if "attach" not in query:
                    return _DeepLink(username="", kind="phone", payload=phones[0])
                # `tg://resolve?phone=<phone>&attach=<bot>` is the `tg:` twin of
                # `t.me/+<phone>?attach=<bot>` and reads the same way: the phone number
                # is the chat the attachment menu opens in, so it addresses no bot and
                # the query is what says which bot the link is about.
                username = ""
            else:
                domains = query.get("domain")
                if not domains or not domains[0]:
                    return None
                username = domains[0]
                # On the `tg://resolve` form `domain` is the address, not a deep-link
                # parameter — `tg://resolve?domain=x` must classify exactly like the bare
                # `t.me/x` it mirrors.
                query.pop("domain")
        else:
            return None

        if not query:
            return _DeepLink(username=username, kind="start", payload="")
        starts = query.get("start")
        if starts and starts[0]:
            # A `start` with a value is the one parameter that wins over every other, and
            # it is checked before the table rather than inside it: a real client opens
            # the bot with `?start=x&startapp=y`, ignoring the parameter it has no use
            # for. An *empty* `?start=` says nothing of the sort, so it does not win —
            # it only survives below, once nothing else has claimed the link.
            return _DeepLink(username=username, kind="start", payload=starts[0])
        for key, kind in _QUERY_KIND_LOOKUP:
            if key in query:
                policy = _LINK_KINDS[kind]
                return _DeepLink(
                    # A `?boost` or `?videochat` names a channel, never this bot, and an
                    # `?attach=` names the chat the menu opens in, so the username is
                    # dropped for both rather than carried where it would read as the
                    # bot's — only `match_by="username"` keeps it.
                    username=username if policy.match_by == _MATCH_USERNAME else "",
                    kind=kind,
                    payload=query[key][0],
                )
        if starts is not None:
            # `?start=` with nothing else to be: the bare `/start` that `t.me/<bot>` is.
            return _DeepLink(username=username, kind="start", payload="")
        return _DeepLink(username=username, kind="unknown_query", payload=parsed.query)

    @property
    def bot_user(self) -> UserState:
        return self.environment.world.bot_user

    def _resolve_member_subject(
        self,
        subject: UserSpec | UserState | int | None,
    ) -> UserState:
        """The `UserState` a membership trigger acts on — the bot itself when ``None``."""
        if subject is None:
            return self.bot_user
        if isinstance(subject, UserState):
            return subject
        user_id = subject if isinstance(subject, int) else subject.id
        return self.environment.world.user(user_id)

    def _guard_not_owner(self, target: UserState) -> None:
        """
        Refuse a promotion or demotion of the chat's owner.

        The rule `promoteChatMember` states and :func:`aiogram.test.modeling._not_the_owner`
        enforces on the real call path: an owner's standing is not the bot's, or a fellow
        administrator's, to take away.

        **Raised as a `WorldLookupError`, not as an `ApiRejection`**, and that is the whole
        distinction between the two paths. On the call path the bot itself asked for the
        promotion, so the refusal is Telegram's answer and the bot's own ``except`` branch
        is the thing under test — `handle_promote` raises `ApiRejection` and the caller sees
        a real `TelegramBadRequest`. Here nothing was asked of the API: a *trigger* is the
        test arranging the world, and arranging something Telegram would never allow is a
        broken setup rather than a modeled outcome. Routing it through the rejection type
        made it convertible, catchable and — worst — indistinguishable from the branch the
        test meant to exercise. The wording stays identical to `handle_promote`'s, so the
        two failures still read alike.
        """
        if self.chat.member(target.id).status == ChatMemberStatus.CREATOR:
            msg = (
                "can't remove chat owner: this trigger arranges the world, and no "
                "administrator can take the owner's standing away, so there is no state "
                "for it to arrange. To test how the bot handles the API refusing its own "
                "promoteChatMember call, have the bot make that call instead."
            )
            raise WorldLookupError(msg)

    async def _change_membership(
        self,
        status: str,
        data: dict[str, Any],
        subject: UserState | None = None,
        *,
        mutate: Callable[[MemberState], None] | None = None,
        service_message: bool = False,
        deliver: bool = True,
    ) -> Any:
        """
        Change a membership, routing by whose it is.

        Telegram delivers the bot's own membership change as ``my_chat_member`` and
        everyone else's as ``chat_member``; a bot that only registers the former must not
        see the latter. ``mutate`` runs between reading the "old" side and the "new"
        one, so `promote`/`demote` can set rights and a custom title alongside the status
        change and have both show up in the same truthful before/after pair.

        ``service_message``, when the chat is a group or a supergroup (see
        `_MEMBER_SERVICE_MESSAGE_CHAT_TYPES`), also stores and feeds the
        `new_chat_members` service message a real join or add delivers alongside the
        membership update — **after** it, mirroring the order Telegram's own apps show
        the two in: the membership transition is the event that happened, the service
        message the group's own announcement of it, so the announcement follows. This
        method's own return value stays the membership update's handler result either
        way — the service message is fed but not awaited for its result, the same as any
        other update a trigger feeds only for its side effects.
        """
        chat = self.chat
        target = subject if subject is not None else self.user
        member = chat.member(target.id)
        user = target.as_user()
        # Read before the mutation and after it, off the one membership the world holds:
        # everything else it carries — a custom title, a tag, granted rights — survives a
        # join or a leave, and rebuilding the "new" side from a subset would drop it.
        old = member.as_chat_member(user, chat.type, self.bot_user.id)
        if mutate is None:
            member.join_or_leave(status)
        else:
            member.set_status(status)
            mutate(member)
        new = member.as_chat_member(user, chat.type, self.bot_user.id)
        event = ChatMemberUpdated(
            chat=chat.as_chat(),
            # GroupAnonymousBot for an anonymous administrator, which
            # no source the toolkit read confirms.
            from_user=self._sender(),
            date=self.environment.world.next_date(),
            old_chat_member=old,
            new_chat_member=new,
        )
        update_id = self._next_update_id()
        # Both updates are one thing the test did, so they share one route scope: a bot
        # that handles the membership transition and ignores the group's announcement of
        # it must not make `assert_handled_by` fail on the update nobody wanted. See
        # `BotTestEnvironment.trigger`.
        with self.environment.trigger():
            if target.id == self.bot_user.id:
                update = Update(update_id=update_id, my_chat_member=event)
            else:
                update = Update(update_id=update_id, chat_member=event)
            result = await self._feed(update, data, deliver=deliver)
            if service_message and chat.type in _MEMBER_SERVICE_MESSAGE_CHAT_TYPES:
                await self._service_message({"new_chat_members": [user]}, data, deliver)
        return result
