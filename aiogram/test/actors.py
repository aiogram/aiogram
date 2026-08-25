from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Iterator
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, NamedTuple
from urllib.parse import parse_qs, urlsplit

from aiogram.enums import ChatMemberStatus, ChatType
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
    MessageReactionCountUpdated,
    MessageReactionUpdated,
    PaidMediaPurchased,
    PollAnswer,
    PreCheckoutQuery,
    ReactionTypeEmoji,
    ReactionTypeUnion,
    ShippingQuery,
    SuccessfulPayment,
    Update,
)

from .mounting import owned_or_copied
from .synthesis import SynthesisContext, synthesize
from .world import (
    BusinessConnectionState,
    ChargeState,
    ChatState,
    CommunityState,
    MemberState,
    QueryKind,
    TopicState,
    UserState,
    WorldLookupError,
    mask,
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
    """

    def __init__(
        self,
        environment: BotTestEnvironment,
        user: UserState,
        chat: ChatState | None = None,
        topic: TopicState | None = None,
        business: BusinessConnectionState | None = None,
    ) -> None:
        self.environment = environment
        self.user = user
        self._chat = chat
        self.topic = topic
        self.business = business

    def in_(
        self,
        chat: ChatSpec | ChatState | int,
        *,
        topic: TopicSpec | TopicState | int | None = None,
        business: BusinessConnectionSpec | BusinessConnectionState | str | None = None,
    ) -> UserActor:
        """
        Bind this user to a chat, optionally to a topic or a business connection.

        Returns a new actor, leaving this one untouched. The binding decides what the
        triggers produce: a plain message, a topic-tagged message, or a business message.

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
        return UserActor(
            self.environment,
            self.user,
            state,
            topic=self._resolve_topic(state, topic),
            business=self.environment.business_connection(business) if business else None,
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
        """FSM context for this actor's binding — the key the dispatcher itself would use."""
        return self.environment.state(
            self.user.id,
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
        """
        message = self._build_message(text=text, fields=self._with_reply_to(fields, reply_to))
        self.chat.add_message(message)
        if self.business is not None:
            return await self._feed(
                Update(update_id=self._next_update_id(), business_message=message),
                data,
            )
        update_id = self._next_update_id()
        if self.chat.type == ChatType.CHANNEL:
            return await self._feed(Update(update_id=update_id, channel_post=message), data)
        return await self._feed(Update(update_id=update_id, message=message), data)

    async def reply(
        self,
        message: Message | int,
        text: str | None = None,
        *,
        fields: dict[str, Any] | None = None,
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
        **data: Any,
    ) -> Any:
        """Edit a message this user sent earlier."""
        changes: dict[str, Any] = {"text": text, **_detached(fields or {}, self.environment.bot)}
        edited = self.chat.update_message(message.message_id, **changes)
        if self.business is not None:
            return await self._feed(
                Update(update_id=self._next_update_id(), edited_business_message=edited),
                data,
            )
        update_id = self._next_update_id()
        if self.chat.type == ChatType.CHANNEL:
            return await self._feed(
                Update(update_id=update_id, edited_channel_post=edited),
                data,
            )
        return await self._feed(Update(update_id=update_id, edited_message=edited), data)

    async def click(
        self,
        target: str | InlineKeyboardButton,
        *,
        message: Message | None = None,
        **data: Any,
    ) -> Any:
        """Press an inline keyboard button of a message the bot actually sent."""
        callback_data = (
            target.callback_data if isinstance(target, InlineKeyboardButton) else target
        )
        if callback_data is None:
            msg = "The button carries no callback_data and cannot be clicked"
            raise WorldLookupError(msg)
        source = message if message is not None else self._find_button_message(callback_data)
        query = CallbackQuery(
            id=self.environment.world.next_query_id(QueryKind.CALLBACK),
            from_user=self.user.as_user(),
            chat_instance=str(self.chat.id),
            message=source,
            data=callback_data,
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), callback_query=query),
            data,
        )

    async def follow_deep_link(
        self,
        target: str | InlineKeyboardButton | None = None,
        *,
        message: Message | None = None,
        validate_payload: bool = True,
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
        if isinstance(target, InlineKeyboardButton):
            url = target.url
            if url is None:
                msg = "The button carries no url and cannot be followed as a deep link"
                raise WorldLookupError(msg)
        else:
            url = target

        scope: Iterable[Message] = (
            [message] if message is not None else reversed(self.chat.messages)
        )
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
        return await UserActor(self.environment, self.user).send(text, **data)

    async def inline_query(self, query: str = "", *, offset: str = "", **data: Any) -> Any:
        inline = InlineQuery(
            id=self.environment.world.next_query_id(QueryKind.INLINE),
            from_user=self.user.as_user(),
            query=query,
            offset=offset,
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), inline_query=inline),
            data,
        )

    async def join(self, *, service_message: bool = True, **data: Any) -> Any:
        """
        Join this chat, producing `chat_member` — and, in a group, the
        `new_chat_members` service message a real join delivers alongside it.

        Pass ``service_message=False`` to get the old single-update behavior back.
        See :meth:`_change_membership` for why the group-only carve-out and the ordering
        between the two updates are what they are.
        """
        return await self._change_membership(
            ChatMemberStatus.MEMBER, data, service_message=service_message
        )

    async def leave(self, **data: Any) -> Any:
        return await self._change_membership(ChatMemberStatus.LEFT, data)

    async def add_bot(self, *, service_message: bool = True, **data: Any) -> Any:
        """
        Add the bot to this chat, producing `my_chat_member` rather than `chat_member` —
        and, in a group, the `new_chat_members` service message a real add delivers
        alongside it (see :meth:`_change_membership`).

        Pass ``service_message=False`` to get the old single-update behavior back.
        """
        return await self._change_membership(
            ChatMemberStatus.MEMBER,
            data,
            subject=self.bot_user,
            service_message=service_message,
        )

    async def remove_bot(self, **data: Any) -> Any:
        return await self._change_membership(ChatMemberStatus.LEFT, data, subject=self.bot_user)

    async def promote(
        self,
        subject: UserSpec | UserState | int | None = None,
        *,
        data: dict[str, Any] | None = None,
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

        return await self._change_membership(
            ChatMemberStatus.ADMINISTRATOR,
            dict(data or {}),
            subject=target,
            mutate=_promote,
        )

    async def demote(
        self,
        subject: UserSpec | UserState | int | None = None,
        *,
        data: dict[str, Any] | None = None,
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

        ``data`` is the dispatcher data to feed the update with, as a mapping rather than
        as ``**kwargs``. It used to be ``**data`` here and ``**rights`` on `promote`, so
        the same keyword on the two twins meant two different things — the one asymmetry in
        the trigger surface that could silently do the wrong thing. Both spell it ``data=``
        now; every other trigger, whose keyword space nothing competes for, keeps its
        ``**data``.
        """
        target = self._resolve_member_subject(subject)
        self._guard_not_owner(target)

        def _demote(member: MemberState) -> None:
            member.rights = None
            member.custom_title = None

        return await self._change_membership(
            ChatMemberStatus.MEMBER,
            dict(data or {}),
            subject=target,
            mutate=_demote,
        )

    async def enable_business_connection(self, **data: Any) -> Any:
        return await self._business_connection_update(is_enabled=True, data=data)

    async def disable_business_connection(self, **data: Any) -> Any:
        return await self._business_connection_update(is_enabled=False, data=data)

    async def delete_business_messages(self, message_ids: list[int], **data: Any) -> Any:
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
        )

    async def add_chat_to_community(
        self,
        community: CommunitySpec | CommunityState | int,
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
        )

    async def remove_chat_from_community(
        self,
        community: CommunitySpec | CommunityState | int,
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
        )

    async def request_join(self, **data: Any) -> Any:
        """Ask to join this chat, producing a `chat_join_request` the bot can act on."""
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
        )

    async def chosen_inline_result(
        self,
        result_id: str,
        query: str = "",
        **data: Any,
    ) -> Any:
        event = self._event(ChosenInlineResult, result_id=result_id, query=query)
        return await self._feed(
            Update(update_id=self._next_update_id(), chosen_inline_result=event),
            data,
        )

    async def shipping_query(self, invoice_payload: str = "payload", **data: Any) -> Any:
        event = self._event(
            ShippingQuery,
            id=self.environment.world.next_query_id(QueryKind.SHIPPING),
            invoice_payload=invoice_payload,
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), shipping_query=event),
            data,
        )

    async def pre_checkout_query(
        self,
        invoice_payload: str = "payload",
        *,
        currency: str = "XTR",
        total_amount: int = 1,
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
        )

    async def pay(
        self,
        invoice_payload: str = "payload",
        *,
        currency: str = "XTR",
        total_amount: int = 1,
        is_subscription: bool = False,
        **data: Any,
    ) -> Any:
        """
        Complete a payment, posting the `successful_payment` message into the chat.

        The charge is recorded, so the handler can refund the id it was given rather than a
        fabricated one, and a star payment credits the bot's balance — see design decision
        D2 of `model-stars-and-gifts`.
        """
        world = self.environment.world
        charge_id = f"charge-{world.next_query_id()}"
        world.stars.charges[charge_id] = ChargeState(
            id=charge_id,
            user_id=self.user.id,
            amount=total_amount,
            is_subscription=is_subscription,
        )
        if currency == "XTR":
            world.stars.record(world.next_query_id(), total_amount, world.next_date(), charge_id)
        payment = self._event(
            SuccessfulPayment,
            invoice_payload=invoice_payload,
            currency=currency,
            total_amount=total_amount,
            telegram_payment_charge_id=charge_id,
            is_recurring=is_subscription or None,
        )
        return await self._service_message({"successful_payment": payment}, data)

    async def purchase_paid_media(self, payload: str = "payload", **data: Any) -> Any:
        event = self._event(PaidMediaPurchased, paid_media_payload=payload)
        return await self._feed(
            Update(update_id=self._next_update_id(), purchased_paid_media=event),
            data,
        )

    async def boost(self, **data: Any) -> Any:
        event = self._event(ChatBoostUpdated)
        return await self._feed(
            Update(update_id=self._next_update_id(), chat_boost=event),
            data,
        )

    async def remove_boost(self, **data: Any) -> Any:
        event = self._event(ChatBoostRemoved)
        return await self._feed(
            Update(update_id=self._next_update_id(), removed_chat_boost=event),
            data,
        )

    async def guest_message(self, text: str | None = None, **data: Any) -> Any:
        """A message from someone who is not a member — the bot sees it as a guest."""
        message = self._build_message(text=text, fields=None)
        self.chat.add_message(message)
        return await self._feed(
            Update(update_id=self._next_update_id(), guest_message=message),
            data,
        )

    async def manage_bot(self, **data: Any) -> Any:
        event = self._event(ManagedBotUpdated, user=self.user.as_user())
        return await self._feed(
            Update(update_id=self._next_update_id(), managed_bot=event),
            data,
        )

    async def update_subscription(self, invoice_payload: str = "payload", **data: Any) -> Any:
        event = self._event(
            BotSubscriptionUpdated,
            user=self.user.as_user(),
            invoice_payload=invoice_payload,
        )
        return await self._feed(
            Update(update_id=self._next_update_id(), subscription=event),
            data,
        )

    async def vote(self, poll_id: str, options: list[int], **data: Any) -> Any:
        """
        Vote in a poll, producing `poll_answer` and recording the vote.

        An empty ``options`` retracts. Telegram never delivers an answer to a closed poll,
        so voting in one raises here — in the test's own code — rather than passing while
        asserting nothing (design decision D5).
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
        )

    async def poll_update(self, poll_id: str, **data: Any) -> Any:
        """The aggregate `poll` update, which is what an anonymous poll delivers."""
        poll = self.environment.world.poll(poll_id)
        return await self._feed(
            Update(update_id=self._next_update_id(), poll=poll.as_poll()),
            data,
        )

    async def react(
        self,
        message: Message | int,
        reaction: list[ReactionTypeUnion] | str | None = None,
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
        )

    async def reaction_count(self, message: Message | int, **data: Any) -> Any:
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
        )

    # -- internals --------------------------------------------------------------------

    def _event(self, event_type: type[Any], **overrides: Any) -> Any:
        """
        Synthesize an event, seeded from this actor's binding.

        The parts a test does not care about come from the same synthesizer the outbound
        side uses, so a Bot API change to any of these types needs no work here.
        """
        world = self.environment.world
        context = SynthesisContext(
            chat=self.chat.as_chat(),
            user=self.user.as_user(),
            date=world.next_date(),
            counter=world.last_update_id,
        )
        event = synthesize(event_type, context, name=event_type.__name__)
        return event.model_copy(update=overrides) if overrides else event

    def _require_business(self) -> BusinessConnectionState:
        if self.business is None:
            msg = (
                "This actor is not bound to a business connection; "
                "bind it with `.in_(chat, business=...)`"
            )
            raise WorldLookupError(msg)
        return self.business

    async def _business_connection_update(self, is_enabled: bool, data: dict[str, Any]) -> Any:
        connection = self._require_business()
        connection.is_enabled = is_enabled
        event = connection.as_business_connection(self.user.as_user())
        return await self._feed(
            Update(update_id=self._next_update_id(), business_connection=event),
            data,
        )

    async def _service_message(self, fields: dict[str, Any], data: dict[str, Any]) -> Any:
        message = self._build_message(text=None, fields=fields)
        self.chat.add_message(message)
        return await self._feed(
            Update(update_id=self._next_update_id(), message=message),
            data,
        )

    def _next_update_id(self) -> int:
        return self.environment.world.next_update_id()

    async def _feed(self, update: Update, data: dict[str, Any]) -> Any:
        return await self.environment.feed(update, **data)

    def _build_message(self, text: str | None, fields: dict[str, Any] | None) -> Message:
        chat = self.chat
        values: dict[str, Any] = {
            "message_id": chat.allocate_message_id(),
            "date": self.environment.world.next_date(),
            "chat": chat.as_chat(),
            "from_user": self.user.as_user(),
        }
        if chat.type == ChatType.CHANNEL:
            # A channel post is attributed to the channel, not to whoever published it.
            values["from_user"] = None
            values["sender_chat"] = chat.as_chat()
            values["author_signature"] = self.user.first_name
        if text is not None:
            values["text"] = text
        if self.topic is not None and not self.topic.is_general:
            values["message_thread_id"] = self.topic.message_thread_id
            values["is_topic_message"] = True
        if self.business is not None:
            values["business_connection_id"] = self.business.id
        values.update(_detached(fields or {}, self.environment.bot))
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
        """
        if reply_to is None:
            return fields
        message = reply_to if isinstance(reply_to, Message) else self._require_message(reply_to)
        return {"reply_to_message": message, **(fields or {})}

    def _require_message(self, message_id: int) -> Message:
        message = self.chat.find_message(message_id)
        if message is None:
            msg = f"Message {message_id} does not exist in chat {self.chat.id}"
            raise WorldLookupError(msg)
        return message

    @staticmethod
    def _iter_buttons(
        scope: Iterable[Message],
    ) -> Iterator[tuple[Message, InlineKeyboardButton]]:
        """Walk message → markup → row → button once, front-to-back, for every searcher."""
        for candidate in scope:
            markup = candidate.reply_markup
            if markup is None:
                continue
            for row in markup.inline_keyboard:
                for button in row:
                    yield candidate, button

    def _find_button_message(self, callback_data: str) -> Message:
        for candidate, button in self._iter_buttons(reversed(self.chat.messages)):
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
                    f"Message {message.message_id} carries no followable (`start`) "
                    f"deep-link button to @{bot_username}, only unfollowable ones: {details}"
                )
            else:
                msg = (
                    f"No message in chat {self.chat.id} carries a followable (`start`) "
                    f"deep-link button to @{bot_username}, only unfollowable ones: {details}"
                )
            raise WorldLookupError(msg)
        if message is not None:
            msg = f"Message {message.message_id} carries no deep-link button to @{bot_username}"
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
        old = member.as_chat_member(user, chat.type)
        member.status = status
        if mutate is not None:
            mutate(member)
        new = member.as_chat_member(user, chat.type)
        event = ChatMemberUpdated(
            chat=chat.as_chat(),
            from_user=self.user.as_user(),
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
                result = await self._feed(Update(update_id=update_id, my_chat_member=event), data)
            else:
                result = await self._feed(Update(update_id=update_id, chat_member=event), data)
            if service_message and chat.type in _MEMBER_SERVICE_MESSAGE_CHAT_TYPES:
                await self._service_message({"new_chat_members": [user]}, data)
        return result
