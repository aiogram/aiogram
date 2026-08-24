from __future__ import annotations

import datetime
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, cast

from pydantic import BaseModel

from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BusinessBotRights,
    BusinessConnection,
    Chat,
    ChatAdministratorRights,
    ChatInviteLink,
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
    ChatMemberUnion,
    ChatPermissions,
    ChatPhoto,
    Community,
    ForumTopic,
    ForumTopicCreated,
    MenuButtonUnion,
    Message,
    Poll,
    PollOption,
    ReactionCount,
    ReactionTypeUnion,
    StarTransaction,
    Sticker,
    StickerSet,
    User,
)

from .mounting import detach, detached_copy, mount
from .waiting import describe_callable, poll_until

if TYPE_CHECKING:
    from aiogram.client.bot import Bot

    from .blueprint import TopicSpec, UserSpec

BASE_DATE: datetime.datetime = datetime.datetime(
    2026,
    1,
    1,
    12,
    0,
    tzinfo=datetime.timezone.utc,
)
"""Fixed point in time every synthesized date is derived from, so tests are reproducible."""

DEFAULT_TOPIC_ICON_COLOR = 0x6FB9F0
GENERAL_TOPIC_NAME = "General"
#: How much of a message's text a failure message shows before cutting it off.
MESSAGE_PREVIEW_LIMIT = 60

#: Administrator rights the Bot API only reports in some chat types, and in which. Outside
#: them the real API leaves the field unset, so a bot that reads
#: ``member.can_post_messages`` in a supergroup gets ``None`` there and must not get a
#: fabricated ``True`` here either.
CHAT_TYPE_SCOPED_RIGHTS: dict[str, frozenset[str]] = {
    "can_post_messages": frozenset({ChatType.CHANNEL}),
    "can_edit_messages": frozenset({ChatType.CHANNEL}),
    "can_manage_direct_messages": frozenset({ChatType.CHANNEL}),
    "can_pin_messages": frozenset({ChatType.GROUP, ChatType.SUPERGROUP}),
    "can_manage_tags": frozenset({ChatType.GROUP, ChatType.SUPERGROUP}),
    "can_manage_topics": frozenset({ChatType.SUPERGROUP}),
}

#: What an administrator promoted the ordinary way can do: everything a moderator needs,
#: minus the two things a chat owner grants deliberately (promoting others, stories).
#: Rights a future Bot API version adds default to ``False`` rather than breaking the call.
_ORDINARY_ADMIN_RIGHTS: dict[str, bool] = {
    "is_anonymous": False,
    "can_manage_chat": True,
    "can_delete_messages": True,
    "can_manage_video_chats": True,
    "can_restrict_members": True,
    "can_promote_members": False,
    "can_change_info": True,
    "can_invite_users": True,
    "can_post_stories": False,
    "can_edit_stories": False,
    "can_delete_stories": False,
    "can_post_messages": True,
    "can_edit_messages": True,
    "can_manage_direct_messages": True,
    "can_pin_messages": True,
    "can_manage_tags": True,
    "can_manage_topics": True,
}


def mask(model: type[BaseModel], source: Any, *, coerce: bool = False) -> dict[str, Any]:
    """
    Read every field of ``model`` off ``source``, by name.

    The Bot API's rights and permissions objects are flat boolean masks, and the fake reads
    them off differently-shaped sources: a rights object, a permissions object, a request
    that simply omits what it does not grant. ``coerce`` turns an unset flag into a denied
    one, which is what an omitted request parameter and an unset permission both mean —
    so the coercion is stated once instead of in each reader's own comprehension.

    Reflecting over ``model_fields`` rather than a hand-kept list is what makes a right a
    future Bot API version adds flow through every one of these readers unchanged.
    """
    return {
        name: bool(getattr(source, name, None)) if coerce else getattr(source, name, None)
        for name in model.model_fields
    }


def scoped_rights(rights: ChatAdministratorRights, chat_type: str) -> ChatAdministratorRights:
    """
    Fit the rights to what the Bot API reports for ``chat_type``.

    The single normalizer, applied where the chat type is in hand — which is only when a
    membership is *read*. A right that cannot exist in a chat reads back as ``None`` there
    however it was set, and a right that *can* exist reads back as a plain boolean even
    when it was left unstated, which is how the real API answers and what a bot writing
    ``if member.can_pin_messages:`` relies on.
    """
    values = mask(ChatAdministratorRights, rights)
    for name, chat_types in CHAT_TYPE_SCOPED_RIGHTS.items():
        values[name] = bool(values[name]) if chat_type in chat_types else None
    return ChatAdministratorRights(**values)


def administrator_rights(**overrides: bool | None) -> ChatAdministratorRights:
    """
    The rights of an ordinary administrator, with ``overrides``.

    The one place the permissive default is built: it is what an administrator declared
    or promoted without explicit rights gets, and it is how a test declares an
    almost-ordinary admin without spelling out seventeen fields::

        administrator_rights(can_delete_messages=False)

    The mask is deliberately *unscoped* — every right the Bot API knows carries a plain
    boolean, including the ones only a channel or only a supergroup reports. Which of them
    a given chat actually reports is :func:`scoped_rights`' job, at the moment the
    membership is read and the chat type is known. Scoping here as well would mean
    declaring a right explicitly grants *fewer* rights than saying nothing at all::

        # In a channel, both of these report `can_post_messages is True`.
        set_member(channel, bot, rights=administrator_rights(can_post_messages=True))
        set_member(channel, bot, status=ChatMemberStatus.ADMINISTRATOR)
    """
    values: dict[str, Any] = dict.fromkeys(ChatAdministratorRights.model_fields, False)
    values.update(_ORDINARY_ADMIN_RIGHTS)
    values.update(overrides)
    return ChatAdministratorRights(**values)


class QueryKind(str, Enum):
    """Kinds of query a trigger can issue and an answer method must consume."""

    CALLBACK = "callback query"
    INLINE = "inline query"
    SHIPPING = "shipping query"
    PRE_CHECKOUT = "pre-checkout query"


class WorldLookupError(LookupError):
    """Raised when the world is asked about a chat, user or message it does not contain."""


def describe_message(message: Message) -> str:
    """
    Identify one stored message in a failure message.

    Shows what a test would recognise it by — its id, a truncated text or caption, and
    whether it carries an inline keyboard — rather than a full dump nobody reads.
    """
    body = message.text if message.text is not None else message.caption
    if body is None:
        preview = "<no text>"
    elif len(body) > MESSAGE_PREVIEW_LIMIT:
        preview = f"{body[:MESSAGE_PREVIEW_LIMIT]!r}..."
    else:
        preview = repr(body)
    keyboard = " [inline keyboard]" if message.reply_markup is not None else ""
    return f"#{message.message_id} {preview}{keyboard}"


def _describe_messages(messages: list[Message], noun: str) -> str:
    """One-line-per-message rendering of a message view, for failure messages."""
    if not messages:
        return f"The {noun} holds no messages."
    lines = [f"The {noun} holds {len(messages)} message(s):"]
    lines.extend(f"  {describe_message(message)}" for message in messages)
    return "\n".join(lines)


async def _wait_for_message(
    view: Callable[[], list[Message]],
    predicate: Callable[[Message], object] | None,
    *,
    noun: str,
    where: str,
    timeout: float,
    interval: float,
) -> Message:
    """
    The polling core behind :meth:`ChatState.wait_for_message` and its topic-scoped twin.

    ``view`` is a callable rather than a list because a topic's messages are a filtered
    view recomputed on every read — capturing the list once would wait on a snapshot taken
    before the message being waited for arrived. ``noun`` and ``where`` are how the failure
    message names the view ("the topic holds…", "…in topic #7 'Support' of chat -100").
    """
    # message id -> what the predicate raised on it during the most recent pass.
    raised: dict[int, Exception] = {}

    def find() -> Message | None:
        raised.clear()
        for message in reversed(view()):
            if predicate is None:
                return message
            try:
                matched = predicate(message)
            except Exception as error:
                raised[message.message_id] = error
                continue
            if matched:
                return message
        return None

    def describe_timeout() -> str:
        wanted = (
            "any message"
            if predicate is None
            else f"a message matching {describe_callable(predicate)}"
        )
        problems = ""
        if raised:
            details = "; ".join(
                f"{type(error).__name__}({str(error)!r}) on message #{message_id}"
                for message_id, error in sorted(raised.items())
            )
            problems = (
                f" The predicate raised on {len(raised)} of them, which counted as no "
                f"match: {details}."
            )
        return (
            f"Timed out after {timeout}s waiting for {wanted} in {where}. "
            f"{_describe_messages(view(), noun)}{problems}"
        )

    return cast(
        Message,
        await poll_until(
            find,
            timeout=timeout,
            interval=interval,
            describe_timeout=describe_timeout,
        ),
    )


@dataclass
class UserState:
    """Mutable state of a single user known to the environment."""

    id: int
    is_bot: bool = False
    first_name: str = "User"
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None

    def as_user(self) -> User:
        return User(
            id=self.id,
            is_bot=self.is_bot,
            first_name=self.first_name,
            last_name=self.last_name,
            username=self.username,
            language_code=self.language_code,
        )


@dataclass
class MemberState:
    """
    Membership of a user in a chat, including what that membership lets them do.

    The rights are stored rather than invented on conversion: ``promoteChatMember`` and a
    blueprint declaration both write them here, so ``getChatMember`` reports exactly what
    was granted — a bot that gates itself on ``can_delete_messages`` sees the right it was
    actually given, not a flattering default.
    """

    user_id: int
    status: str = ChatMemberStatus.MEMBER
    #: Administrators carry a custom title; regular members carry a tag. The Bot API puts
    #: them on different `ChatMember` variants, so they are not interchangeable.
    custom_title: str | None = None
    tag: str | None = None
    until_date: datetime.datetime | None = None
    #: What an administrator (or an anonymous owner) may do. ``None`` means "not stated",
    #: which reads back as the ordinary administrator rights of the chat's type.
    rights: ChatAdministratorRights | None = None
    #: What a restricted member may do. ``None`` means every permission is denied, which is
    #: what a restriction with no permissions passed amounts to.
    permissions: ChatPermissions | None = None

    @property
    def is_present(self) -> bool:
        return self.status not in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}

    def as_chat_member(self, user: User, chat_type: str) -> ChatMemberUnion:
        """
        The Bot API's view of this membership in a chat of ``chat_type``.

        The chat type is a parameter because the answer depends on it: the Bot API reports
        ``can_post_messages`` only for channels and ``can_manage_topics`` only for
        supergroups, so a variant built without knowing where the member is cannot be
        truthful about either.
        """
        if self.status == ChatMemberStatus.CREATOR:
            return ChatMemberOwner(
                user=user,
                is_anonymous=self.rights.is_anonymous if self.rights is not None else False,
                custom_title=self.custom_title,
            )
        if self.status == ChatMemberStatus.ADMINISTRATOR:
            declared = self.rights if self.rights is not None else administrator_rights()
            return ChatMemberAdministrator(
                user=user,
                custom_title=self.custom_title,
                can_be_edited=False,
                **mask(ChatAdministratorRights, scoped_rights(declared, chat_type)),
            )
        if self.status == ChatMemberStatus.RESTRICTED:
            permissions = self.permissions if self.permissions is not None else ChatPermissions()
            return ChatMemberRestricted(
                user=user,
                is_member=True,
                tag=self.tag,
                until_date=self.until_date or BASE_DATE,
                # An unset permission is a denied one: the Bot API's own restricted member
                # carries plain booleans, while a request omits what it does not grant.
                **mask(ChatPermissions, permissions, coerce=True),
            )
        if self.status == ChatMemberStatus.KICKED:
            return ChatMemberBanned(user=user, until_date=self.until_date or BASE_DATE)
        if self.status == ChatMemberStatus.LEFT:
            return ChatMemberLeft(user=user)
        return ChatMemberMember(user=user, tag=self.tag, until_date=self.until_date)


@dataclass
class TopicState:
    """
    A forum topic.

    Its messages are a filtered view over the chat's single message list — a second list
    could drift from the first on any edit, delete or forward that forgot to update both.
    """

    message_thread_id: int | None
    name: str = GENERAL_TOPIC_NAME
    icon_color: int = DEFAULT_TOPIC_ICON_COLOR
    icon_custom_emoji_id: str | None = None
    is_closed: bool = False
    is_hidden: bool = False
    is_general: bool = False
    chat: ChatState | None = field(default=None, repr=False, compare=False)

    @property
    def messages(self) -> list[Message]:
        if self.chat is None:  # pragma: no cover - a topic is always registered on a chat
            return []
        if self.is_general:
            return [item for item in self.chat.messages if item.message_thread_id is None]
        return [
            item for item in self.chat.messages if item.message_thread_id == self.message_thread_id
        ]

    @property
    def label(self) -> str:
        """How a failure message names this topic."""
        # A topic is always registered on a chat; a hand-built one still names itself.
        chat = "" if self.chat is None else f" of chat {self.chat.id}"
        if self.is_general:
            return f"the General topic{chat}"
        return f"topic #{self.message_thread_id} {self.name!r}{chat}"

    async def wait_for_message(
        self,
        predicate: Callable[[Message], object] | None = None,
        *,
        timeout: float = 5.0,
        interval: float = 0.01,
    ) -> Message:
        """
        Wait until a message matching ``predicate`` is in **this topic**, and return it.

        :meth:`ChatState.wait_for_message` scoped to one topic: it waits on the same
        filtered view :attr:`messages` exposes, so a message posted into a sibling topic
        never satisfies it, and the failure message enumerates this topic rather than the
        whole forum. Everything else — matching against messages that are already there,
        a raising predicate counting as "no match", the reporting of what it raised — works
        exactly as it does for a chat, because it is the same implementation.

        :raises aiogram.test.errors.WaitTimeoutError: if no such message ever appeared.
        """
        return await _wait_for_message(
            lambda: self.messages,
            predicate,
            noun="topic",
            where=self.label,
            timeout=timeout,
            interval=interval,
        )

    def describe_messages(self) -> str:
        """One-line-per-message rendering of the topic, for failure messages."""
        return _describe_messages(self.messages, "topic")

    def as_forum_topic(self) -> ForumTopic:
        if self.message_thread_id is None:
            msg = "The General topic is not represented as a ForumTopic by the Bot API"
            raise WorldLookupError(msg)
        return ForumTopic(
            message_thread_id=self.message_thread_id,
            name=self.name,
            icon_color=self.icon_color,
            icon_custom_emoji_id=self.icon_custom_emoji_id,
        )


@dataclass
class BusinessConnectionState:
    """A business account connection the bot acts on behalf of."""

    id: str
    user_id: int
    user_chat_id: int
    is_enabled: bool = True
    can_reply: bool = True
    rights: BusinessBotRights | None = None
    date: datetime.datetime = BASE_DATE

    def as_business_connection(self, user: User) -> BusinessConnection:
        # The rights are the world's own object, and a result gets mounted — see the note
        # on `StickerSetState.as_sticker_set`.
        return BusinessConnection(
            id=self.id,
            user=user,
            user_chat_id=self.user_chat_id,
            date=self.date,
            is_enabled=self.is_enabled,
            can_reply=self.can_reply,
            rights=detached_copy(self.rights),
        )


@dataclass
class StickerSetState:
    """
    A sticker set, keyed by name as Telegram keys them.

    Stickers are stored as the generated ``Sticker`` type directly: nothing in this cluster
    edits one, so a parallel state class would be a wrapper with no fields of its own — see
    design decision D2.
    """

    name: str
    title: str
    sticker_type: str = "regular"
    stickers: list[Sticker] = field(default_factory=list)

    def index_of(self, file_id: str) -> int:
        for index, sticker in enumerate(self.stickers):
            if sticker.file_id == file_id:
                return index
        msg = f"Sticker {file_id!r} is not in set {self.name!r}"
        raise WorldLookupError(msg)

    def as_sticker_set(self) -> StickerSet:
        """
        The Bot API's view of this set, carrying copies of the stickers.

        A result is mounted to the calling bot, and the world's stickers are *value*
        objects a test compares against declared ones — pydantic counts a binding in
        ``__eq__`` while hiding it from ``__repr__``, so handing out the stored instances
        would bind the world's own state and break ``set.stickers == DECLARED`` with two
        identical-looking sides. Messages are the deliberate exception: their identity
        with what the chat holds is the feature.
        """
        return StickerSet(
            name=self.name,
            title=self.title,
            sticker_type=self.sticker_type,
            stickers=detached_copy(self.stickers),
        )


@dataclass
class ChargeState:
    """
    A star payment the environment recorded.

    Refunds and subscription edits both key on ``telegram_payment_charge_id``, so both
    flags live here rather than in separate registries — "already refunded" and "unknown
    charge" then collapse into one lookup, as they do for outstanding queries.
    """

    id: str
    user_id: int
    amount: int
    is_subscription: bool = False
    is_refunded: bool = False
    is_subscription_canceled: bool = False


@dataclass
class StarTransactionState:
    """One movement of stars. Positive credits the bot, negative debits it."""

    id: str
    amount: int
    date: datetime.datetime
    charge_id: str | None = None

    def as_star_transaction(self) -> StarTransaction:
        return StarTransaction(id=self.id, amount=self.amount, date=self.date)


@dataclass
class StarLedger:
    """
    The bot's stars.

    The balance is *derived* from the transactions and never stored beside them — an
    aggregate kept next to its source drifts the first time a path updates one and not the
    other, and money is the worst place to allow that. See design decision D1.
    """

    opening_balance: int = 0
    transactions: list[StarTransactionState] = field(default_factory=list)
    charges: dict[str, ChargeState] = field(default_factory=dict)

    @property
    def balance(self) -> int:
        return self.opening_balance + sum(item.amount for item in self.transactions)

    def record(
        self,
        transaction_id: str,
        amount: int,
        date: datetime.datetime,
        charge_id: str | None = None,
    ) -> StarTransactionState:
        transaction = StarTransactionState(
            id=transaction_id,
            amount=amount,
            date=date,
            charge_id=charge_id,
        )
        self.transactions.append(transaction)
        return transaction

    def charge(self, charge_id: str) -> ChargeState:
        charge = self.charges.get(charge_id)
        if charge is None:
            msg = f"No star payment with charge id {charge_id!r} was recorded"
            raise WorldLookupError(msg)
        return charge


@dataclass
class OwnedGiftState:
    """
    A gift somebody owns.

    The owner is a field rather than the key of a per-owner mapping, so transferring is a
    write instead of a move between containers, and the three readers differ only by which
    owner they filter on — see design decision D4.
    """

    owned_gift_id: str
    gift_id: str
    owner_id: int
    star_count: int
    send_date: datetime.datetime = BASE_DATE
    is_unique: bool = False


@dataclass
class InviteLinkState:
    """
    One invite link of a chat.

    ``is_primary`` lives on the link rather than in a separate pointer, so "the primary
    link" is a filter that cannot dangle after a revoke — see design decision D1.
    """

    invite_link: str
    creator_id: int
    name: str | None = None
    expire_date: datetime.datetime | None = None
    member_limit: int | None = None
    creates_join_request: bool = False
    subscription_period: int | None = None
    subscription_price: int | None = None
    is_primary: bool = False
    is_revoked: bool = False

    def as_chat_invite_link(self, creator: User) -> ChatInviteLink:
        return ChatInviteLink(
            invite_link=self.invite_link,
            creator=creator,
            creates_join_request=self.creates_join_request,
            is_primary=self.is_primary,
            is_revoked=self.is_revoked,
            name=self.name,
            expire_date=self.expire_date,
            member_limit=self.member_limit,
            subscription_period=self.subscription_period,
            subscription_price=self.subscription_price,
        )


@dataclass
class PollState:
    """
    A poll and the votes cast in it.

    ``votes`` is the single source of truth: per-option counts are computed on conversion
    rather than stored alongside, so they cannot drift out of step with the voters — see
    design decision D1.
    """

    id: str
    question: str
    options: list[str]
    is_anonymous: bool = True
    type: str = "regular"
    allows_multiple_answers: bool = False
    allows_revoting: bool = False
    members_only: bool = False
    correct_option_id: int | None = None
    explanation: str | None = None
    is_closed: bool = False
    votes: dict[int, list[int]] = field(default_factory=dict)

    def vote_count(self, option_id: int) -> int:
        return sum(1 for chosen in self.votes.values() if option_id in chosen)

    def as_poll(self) -> Poll:
        return Poll(
            id=self.id,
            question=self.question,
            options=[
                PollOption(persistent_id=str(index), text=text, voter_count=self.vote_count(index))
                for index, text in enumerate(self.options)
            ],
            total_voter_count=len(self.votes),
            is_closed=self.is_closed,
            is_anonymous=self.is_anonymous,
            type=self.type,
            allows_multiple_answers=self.allows_multiple_answers,
            allows_revoting=self.allows_revoting,
            members_only=self.members_only,
            correct_option_id=self.correct_option_id,
            correct_option_ids=None
            if self.correct_option_id is None
            else [self.correct_option_id],
            explanation=self.explanation,
        )


@dataclass
class CommunityState:
    """A community and the chats attached to it."""

    id: int
    name: str
    chat_ids: list[int] = field(default_factory=list)

    def as_community(self) -> Community:
        return Community(id=self.id, name=self.name)


def derive_message(original: Message, **changes: Any) -> Message:
    """
    A copy of ``original`` with ``changes`` applied — a genuinely fresh message.

    Every message the world derives from another goes through here: an edit replacing the
    message it derives from, a forward and a copy landing in some other chat. They differ
    in where the result goes, not in what it is, and what it is has to be said once:
    :meth:`~pydantic.BaseModel.model_copy` carries the original's ``_bot`` over, which makes
    :func:`~aiogram.test.mounting.mount` prune the new message at its root and leave
    everything the change brought along — a new chat, a new sender, a forward origin, a new
    keyboard — unbound, raising on its first shortcut. Detaching says what a copy is, and
    the mount that follows binds all of it.

    The ``changes`` are copied on the way in, for the reason
    :func:`~aiogram.test.mounting.detached_copy` gives: an edit carries the caller's own
    ``reply_markup`` or entities, and what the world stores must not be an object the code
    under test still holds — it would be bound to a bot the moment the edited message is
    handed back.
    """
    return detach(original.model_copy(update=detached_copy(changes)))


@dataclass
class ChatState:
    """Mutable state of a single chat: its members, its messages and what is pinned."""

    id: int
    type: str = ChatType.PRIVATE
    title: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    members: dict[int, MemberState] = field(default_factory=dict)
    messages: list[Message] = field(default_factory=list)
    deleted_message_ids: set[int] = field(default_factory=set)
    pinned_message_ids: list[int] = field(default_factory=list)
    join_requests: set[int] = field(default_factory=set)
    #: message id -> user id -> that user's current reactions.
    reactions: dict[int, dict[int, list[ReactionTypeUnion]]] = field(default_factory=dict)
    last_message_id: int = 0
    description: str | None = None
    permissions: ChatPermissions | None = None
    photo: ChatPhoto | None = None
    sticker_set_name: str | None = None
    invite_links: list[InviteLinkState] = field(default_factory=list)
    is_forum: bool = False
    topics: dict[int, TopicState] = field(default_factory=dict)
    community_id: int | None = None
    general_topic: TopicState = field(
        default_factory=lambda: TopicState(message_thread_id=None, is_general=True),
    )
    #: The world this chat is part of, installed by :class:`ChatRegistry` when the chat is
    #: registered. Excluded from equality and repr — it is wiring, not state a test asserts
    #: on, and comparing it would recurse straight back into this chat.
    world: World | None = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        self.general_topic.chat = self

    @property
    def bound_bot(self) -> Bot | None:
        """
        The bot every message stored here is bound to, derived from the world.

        Derived rather than stored: a copy of the owner kept per chat has to be refreshed
        whenever either side changes, and a chat that missed a refresh silently stores
        unbound messages. There is one owner — the world's — and this reads it.
        """
        return self.world.bound_bot if self.world is not None else None

    def as_chat(self) -> Chat:
        return Chat(
            id=self.id,
            type=self.type,
            title=self.title,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            is_forum=self.is_forum or None,
        )

    def allocate_message_id(self) -> int:
        self.last_message_id += 1
        return self.last_message_id

    def add_message(self, message: Message) -> Message:
        """
        Store a message, bound to the bot this world belongs to.

        Storage is the moment an object *enters* the fake world, and it is the only such
        moment for every producer at once — a user actor's message, a modeled send, a
        service message no result ever carries. Binding here is therefore what makes the
        rule "everything the world holds is usable" hold without a special case per
        producer: ``chat.messages[-1].answer(...)`` works whoever put the message there.
        """
        self.messages.append(message)
        return self._bind(message)

    def find_message(self, message_id: int) -> Message | None:
        for message in self.messages:
            if message.message_id == message_id:
                return message
        return None

    def require_message(self, message_id: int) -> Message:
        message = self.find_message(message_id)
        if message is None:
            msg = f"Message {message_id} does not exist in chat {self.id}"
            raise WorldLookupError(msg)
        return message

    def update_message(self, message_id: int, **changes: Any) -> Message:
        """Replace a stored message with an edited copy — API types are frozen."""
        message = self.require_message(message_id)
        edited = derive_message(message, **changes)
        self.messages[self.messages.index(message)] = edited
        return self._bind(edited)

    def add_derived(self, original: Message, **changes: Any) -> Message:
        """Store a copy of ``original`` in this chat — see :func:`derive_message`."""
        return self.add_message(derive_message(original, **changes))

    def _bind(self, message: Message) -> Message:
        """Mount a message and everything new in it to the world's bot, if there is one."""
        if self.bound_bot is not None:
            mount(message, self.bound_bot)
        return message

    def delete_message(self, message_id: int) -> None:
        message = self.require_message(message_id)
        self.messages.remove(message)
        self.deleted_message_ids.add(message_id)
        if message_id in self.pinned_message_ids:
            self.pinned_message_ids.remove(message_id)

    async def wait_for_message(
        self,
        predicate: Callable[[Message], object] | None = None,
        *,
        timeout: float = 5.0,
        interval: float = 0.01,
    ) -> Message:
        """
        Wait until a message matching ``predicate`` is in this chat, and return it.

        The specialized form of :meth:`aiogram.test.BotTestEnvironment.wait_for` for the
        case that dominates tests of bots with background work: something the test did not
        await is expected to post into this chat. Between checks it yields to the event
        loop, which is what lets those tasks run at all.

        ``predicate`` is matched against **every** message the chat holds, not only the
        ones that arrive after the call: a message that is already there satisfies the
        wait immediately, so a test never has to race the send it is waiting for. When
        several match, the newest one is returned. ``predicate=None`` waits for any
        message::

            reply = await bot_chat.wait_for_message(lambda m: m.text.startswith("Night"))

        A predicate that *raises* on a message counts as "does not match" rather than
        failing the wait, because a chat holds messages of every shape: the natural
        ``m.text.startswith(...)`` above blows up on the first service message —
        ``forum_topic_created``, a pin — whose ``text`` is ``None``, and a wait has no
        business dying on a message it was not asking about. The exceptions are not
        swallowed, though: if the wait times out, the failure message reports what the
        predicate raised and on which message, so a predicate that is simply buggy still
        fails visibly and with its real cause.

        :raises aiogram.test.errors.WaitTimeoutError: if no such message ever appeared.
        """
        return await _wait_for_message(
            lambda: self.messages,
            predicate,
            noun="chat",
            where=f"chat {self.id}",
            timeout=timeout,
            interval=interval,
        )

    def describe_messages(self) -> str:
        """One-line-per-message rendering of the chat, for failure messages."""
        return _describe_messages(self.messages, "chat")

    def invite_link(self, url: str) -> InviteLinkState:
        for link in self.invite_links:
            if link.invite_link == url:
                return link
        msg = f"Invite link {url} does not exist in chat {self.id}"
        raise WorldLookupError(msg)

    @property
    def primary_invite_link(self) -> InviteLinkState | None:
        """The chat's current primary link, if one has ever been exported."""
        for link in self.invite_links:
            if link.is_primary and not link.is_revoked:
                return link
        return None

    def replace_primary_invite_link(self, url: str, creator_id: int) -> InviteLinkState:
        """
        Revoke the current primary link and install a new one.

        Both `exportChatInviteLink` and revoking the primary link go through here, so the
        "exactly one active primary" invariant has a single owner.
        """
        current = self.primary_invite_link
        if current is not None:
            current.is_revoked = True
        link = InviteLinkState(invite_link=url, creator_id=creator_id, is_primary=True)
        self.invite_links.append(link)
        return link

    def reactions_for(self, message_id: int) -> dict[int, list[ReactionTypeUnion]]:
        """Who reacted to this message, and with what."""
        return self.reactions.get(message_id, {})

    def set_reaction(
        self,
        message_id: int,
        user_id: int,
        reaction: list[ReactionTypeUnion],
    ) -> None:
        """
        Replace a reactor's reactions; an empty list removes them entirely.

        The reactions are stored as copies. The very same instances travel on the update
        that announces them, where they are mounted to the bot like everything an update
        carries — and pydantic counts that binding in ``__eq__`` while hiding it from
        ``__repr__``. Reactions, unlike messages, are value objects a test compares against
        plainly declared ones::

            assert chat.reactions_for(message.message_id) == {alice.id: [THUMBS_UP]}

        Sharing the instances would make that assertion fail with two identical-looking
        sides, so the store keeps its own unbound copies.
        """
        per_message = self.reactions.setdefault(message_id, {})
        if reaction:
            per_message[user_id] = detached_copy(list(reaction))
        else:
            per_message.pop(user_id, None)

    def reaction_counts(self, message_id: int) -> list[ReactionCount]:
        """Aggregate reactors into counts, derived on read rather than stored."""
        totals: dict[str, tuple[ReactionTypeUnion, int]] = {}
        for reactions in self.reactions_for(message_id).values():
            for reaction in reactions:
                key = reaction.model_dump_json()
                current = totals.get(key)
                totals[key] = (reaction, (current[1] if current else 0) + 1)
        # Copies again, for the reason `set_reaction` explains: a count travels outwards,
        # on an update or in a result, and gets mounted there.
        return [
            ReactionCount(type=detached_copy(reaction), total_count=count)
            for reaction, count in totals.values()
        ]

    def topic(self, message_thread_id: int | None) -> TopicState:
        if message_thread_id is None:
            return self.general_topic
        topic = self.topics.get(message_thread_id)
        if topic is None:
            msg = f"Topic {message_thread_id} does not exist in chat {self.id}"
            raise WorldLookupError(msg)
        return topic

    def member(self, user_id: int) -> MemberState:
        member = self.members.get(user_id)
        if member is None:
            member = MemberState(user_id=user_id, status=ChatMemberStatus.LEFT)
            self.members[user_id] = member
        return member


#: Key of a stored command list: the scope's own fields plus the language code.
ScopeKey = tuple[Any, ...]


def scope_key(scope: Any, language_code: str | None) -> ScopeKey:
    """
    Hashable key for a ``BotCommandScope`` plus a language.

    Built from every field the scope member declares rather than a hand-read list, so a
    future variant carrying a new identifying field keys correctly instead of colliding
    with its siblings — see design decision D5.

    An omitted scope keys identically to an explicit ``BotCommandScopeDefault``, because
    the Bot API treats them as the same scope.
    """
    if scope is None:
        scope = BotCommandScopeDefault()
    values = tuple((name, getattr(scope, name)) for name in sorted(type(scope).model_fields))
    return (*values, language_code or None)


@dataclass
class BotProfileState:
    """
    The bot's own configuration: what ``setMy*`` writes and ``getMy*`` reads back.

    Commands are keyed exactly; the localized texts and the menu button fall back to their
    default entry, matching what the Bot API documents for each — see design decision D2.
    """

    commands: dict[ScopeKey, list[BotCommand]] = field(default_factory=dict)
    name: dict[str | None, str] = field(default_factory=dict)
    description: dict[str | None, str] = field(default_factory=dict)
    short_description: dict[str | None, str] = field(default_factory=dict)
    default_admin_rights: dict[bool, ChatAdministratorRights] = field(default_factory=dict)
    menu_buttons: dict[int | None, MenuButtonUnion] = field(default_factory=dict)

    def localized(self, texts: dict[str | None, str], language_code: str | None) -> str | None:
        """A dedicated text for this language, else the one shown to everyone else."""
        return texts.get(language_code or None, texts.get(None))

    def set_localized(
        self,
        texts: dict[str | None, str],
        language_code: str | None,
        value: str | None,
    ) -> None:
        """An empty value removes the dedicated entry so the default applies again."""
        key = language_code or None
        if value:
            texts[key] = value
        else:
            texts.pop(key, None)


class ChatRegistry(dict[int, ChatState]):
    """
    The world's chats, which hand every chat put into them a way back to the world.

    A chat needs the world to know which bot its messages are bound to, and there is
    exactly one moment when a chat becomes part of a world: when it is put here. Doing the
    wiring at that moment rather than in a later sweep is what lets every reader be a plain
    reader — ``world.chats.get(id)`` is as safe as :meth:`World.chat`, and a test that
    drops a chat straight into the mapping gets a working one.
    """

    def __init__(self, world: World) -> None:
        super().__init__()
        self.world = world

    def __setitem__(self, chat_id: int, chat: ChatState) -> None:
        chat.world = self.world
        super().__setitem__(chat_id, chat)


@dataclass
class World:
    """Everything the environment knows: the bot, the users, the chats and the counters."""

    bot_user: UserState
    users: dict[int, UserState] = field(default_factory=dict)
    chats: dict[int, ChatState] = field(default_factory=dict)
    business_connections: dict[str, BusinessConnectionState] = field(default_factory=dict)
    communities: dict[int, CommunityState] = field(default_factory=dict)
    profile: BotProfileState = field(default_factory=BotProfileState)
    #: Query ids issued by a trigger and not yet answered, by query kind.
    pending_queries: dict[str, str] = field(default_factory=dict)
    polls: dict[str, PollState] = field(default_factory=dict)
    #: Downloadable content by ``file_id``. Declared on a blueprint, or registered when a
    #: handler uploads a file whose input carries its bytes.
    files: dict[str, bytes] = field(default_factory=dict)
    stars: StarLedger = field(default_factory=StarLedger)
    owned_gifts: dict[str, OwnedGiftState] = field(default_factory=dict)
    sticker_sets: dict[str, StickerSetState] = field(default_factory=dict)
    last_update_id: int = 0
    last_query_id: int = 0
    #: The bot this world belongs to; see :meth:`bind`.
    bound_bot: Bot | None = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        declared = self.chats
        self.chats = ChatRegistry(self)
        for chat_id, chat in declared.items():
            self.chats[chat_id] = chat

    def bind(self, bot: Bot) -> None:
        """
        Declare which bot owns this world, so stored objects can be bound to it.

        Called once by :class:`aiogram.test.BotTestEnvironment` as soon as it has a bot.
        A world without an owner still works — it just stores unbound objects, which is
        all a world built and inspected on its own can offer.

        One assignment, and every chat follows: a chat reads the owner off the world it was
        registered in rather than keeping a copy that would have to be kept in step.
        """
        self.bound_bot = bot

    def user(self, user_id: int) -> UserState:
        if user_id == self.bot_user.id:
            return self.bot_user
        user = self.users.get(user_id)
        if user is None:
            msg = f"User {user_id} is not declared in the blueprint"
            raise WorldLookupError(msg)
        return user

    def chat(self, chat_id: int) -> ChatState:
        chat = self.chats.get(chat_id)
        if chat is None:
            msg = f"Chat {chat_id} is not declared in the blueprint"
            raise WorldLookupError(msg)
        return chat

    def ensure_private_chat(self, user: UserState) -> ChatState:
        """
        The user's private chat with the bot, opened if it does not exist yet.

        Every Telegram user *can* open a private chat with a bot, and some actions — tapping
        a `/start` deep link, most of all — open it as a side effect. A blueprint that did
        not declare one is therefore not saying "this user has no private chat"; it is only
        saying the test did not need to name it. So the chat is created here, from the same
        description :meth:`aiogram.test.Blueprint.add_private_chat` declares one from,
        rather than the world refusing an interaction Telegram itself would allow.
        """
        chat = self.chats.get(user.id)
        if chat is None:
            chat = ChatState(
                **private_chat_shape(user),
                members={user.id: MemberState(user_id=user.id)},
            )
            # Registering is what hands the chat the world, so its messages are bound like
            # any declared chat's.
            self.chats[user.id] = chat
        return chat

    def business_connection(self, connection_id: str) -> BusinessConnectionState:
        connection = self.business_connections.get(connection_id)
        if connection is None:
            msg = f"business connection {connection_id} not found"
            raise WorldLookupError(msg)
        return connection

    def community(self, community_id: int) -> CommunityState:
        community = self.communities.get(community_id)
        if community is None:
            msg = f"Community {community_id} is not declared in the blueprint"
            raise WorldLookupError(msg)
        return community

    def next_update_id(self) -> int:
        self.last_update_id += 1
        return self.last_update_id

    def sticker_set(self, name: str) -> StickerSetState:
        sticker_set = self.sticker_sets.get(name)
        if sticker_set is None:
            msg = f"Sticker set {name!r} does not exist in this environment"
            raise WorldLookupError(msg)
        return sticker_set

    def sticker_set_containing(self, file_id: str) -> StickerSetState:
        """`deleteStickerFromSet` names no set, so the sticker has to identify one."""
        for sticker_set in self.sticker_sets.values():
            if any(sticker.file_id == file_id for sticker in sticker_set.stickers):
                return sticker_set
        msg = f"Sticker {file_id!r} is not in any sticker set in this environment"
        raise WorldLookupError(msg)

    def owned_gift(self, owned_gift_id: str) -> OwnedGiftState:
        gift = self.owned_gifts.get(owned_gift_id)
        if gift is None:
            msg = f"Gift {owned_gift_id!r} is not owned by anybody in this environment"
            raise WorldLookupError(msg)
        return gift

    def gifts_of(self, owner_id: int) -> list[OwnedGiftState]:
        return [gift for gift in self.owned_gifts.values() if gift.owner_id == owner_id]

    def poll(self, poll_id: str) -> PollState:
        poll = self.polls.get(poll_id)
        if poll is None:
            msg = f"Poll {poll_id} is not known to this environment"
            raise WorldLookupError(msg)
        return poll

    def next_query_id(self, kind: str | None = None) -> str:
        """Allocate a query id, recording it as outstanding when it belongs to a kind."""
        self.last_query_id += 1
        query_id = str(self.last_query_id)
        if kind is not None:
            self.pending_queries[query_id] = kind
        return query_id

    def answer_query(self, kind: str, query_id: str) -> None:
        """
        Consume an outstanding query, failing the way Telegram does when there is none.

        Popping rather than marking answered makes "already answered" and "never issued"
        the same code path, which is also how Telegram reports them.
        """
        if self.pending_queries.pop(query_id, None) != kind:
            msg = (
                "query is too old and response timeout expired or query ID is invalid "
                f"({kind} {query_id!r} is not outstanding)"
            )
            raise WorldLookupError(msg)

    def next_date(self) -> datetime.datetime:
        return BASE_DATE + datetime.timedelta(seconds=self.last_update_id)


def private_chat_shape(user: UserState | UserSpec) -> dict[str, Any]:
    """
    What a private chat between the bot and ``user`` looks like.

    A private chat is described in two places — declared by
    :meth:`aiogram.test.Blueprint.add_private_chat`, opened on demand by
    :meth:`World.ensure_private_chat` — and the two must agree, or a user whose chat the
    blueprint happened to declare would live in a differently-shaped chat than one whose
    chat a deep link opened. The shape is stated here; each caller only adds the membership
    in the type it deals in.
    """
    return {
        "id": user.id,
        "type": ChatType.PRIVATE,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


def resolve_topic(chat: ChatState, topic: TopicSpec | TopicState | int) -> TopicState:
    """
    The topic a declaration, a state or a thread id names, within ``chat``.

    A topic can be addressed by any of the three, and every caller that accepts one accepts
    all three; an unknown thread id fails here rather than producing an untagged message.
    """
    if isinstance(topic, TopicState):
        return topic
    thread_id = topic if isinstance(topic, int) else topic.message_thread_id
    return chat.topic(thread_id)


def create_topic(
    chat: ChatState,
    *,
    name: str,
    date: datetime.datetime,
    icon_color: int = DEFAULT_TOPIC_ICON_COLOR,
    icon_custom_emoji_id: str | None = None,
    from_user: User | None = None,
) -> TopicState:
    """
    Open a forum topic the way Telegram does.

    A topic is numbered by the message id of the ``forum_topic_created`` service message
    that opened it, so blueprint-declared topics and topics created through the API are
    indistinguishable — both go through here.
    """
    message_thread_id = chat.allocate_message_id()
    chat.is_forum = True
    chat.add_message(
        Message(
            message_id=message_thread_id,
            date=date,
            chat=chat.as_chat(),
            from_user=from_user,
            message_thread_id=message_thread_id,
            is_topic_message=True,
            forum_topic_created=ForumTopicCreated(
                name=name,
                icon_color=icon_color,
                icon_custom_emoji_id=icon_custom_emoji_id,
            ),
        ),
    )
    topic = TopicState(
        message_thread_id=message_thread_id,
        name=name,
        icon_color=icon_color,
        icon_custom_emoji_id=icon_custom_emoji_id,
        chat=chat,
    )
    chat.topics[message_thread_id] = topic
    return topic
