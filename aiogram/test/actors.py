from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, Any, NamedTuple
from urllib.parse import parse_qs, urlsplit

from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import (
    BotSubscriptionUpdated,
    BusinessMessagesDeleted,
    CallbackQuery,
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

from .overrides import fresh_result
from .synthesis import SynthesisContext, synthesize
from .world import (
    BusinessConnectionState,
    ChargeState,
    ChatState,
    CommunityState,
    QueryKind,
    TopicState,
    UserState,
    WorldLookupError,
    resolve_topic,
)

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext

    from .blueprint import BusinessConnectionSpec, ChatSpec, CommunitySpec, TopicSpec
    from .environment import BotTestEnvironment


class _DeepLink(NamedTuple):
    """A URL button parsed as a Telegram deep link, regardless of which bot it targets."""

    username: str
    kind: str
    """
    One of ``"start"``, ``"startgroup"``, ``"startapp"``, ``"startchannel"``,
    ``"startattach"``, ``"attach"``, ``"invite"``, ``"joinchat"`` or ``"extra_path"``.
    """
    payload: str


class _LinkKindPolicy(NamedTuple):
    """How a parsed deep-link `kind` behaves in `follow_deep_link`."""

    resolvable: bool
    """
    Whether `username` is meaningful for this kind. False for a chat invite link or a
    link with extra path segments, where the parsed username should never be compared
    against the bot's — `follow_deep_link` rejects these before that comparison, and the
    automatic scan never treats them as targeting this bot in the first place.
    """

    followable: bool
    """Whether `follow_deep_link` can replay this kind as a `/start` — only `start`."""

    rejection: str
    """
    The message raised when this kind is used as an explicit target, or is the reason
    given when it is the only kind the automatic scan finds. A format string taking
    `url` and `kind`; unused (left empty) for the one followable kind.
    """


def _unresolvable_rejection(reason: str) -> str:
    return (
        f"{{url!r}} is {reason}, not a bot deep link; only "
        f"`t.me/<username>[?start=<payload>]` and "
        f"`tg://resolve?domain=<username>[&start=<payload>]` links can be followed here"
    )


def _unfollowable_start_rejection(reason: str) -> str:
    return (
        f"{{url!r}} is a `{{kind}}` link, which {reason} in a real Telegram client; only "
        f"`start` deep links can be followed here — Mini Apps, channel targets and the "
        f"attachment menu are not simulated"
    )


# Single source of truth for how each parsed `kind` behaves: whether `username` is
# meaningful for it, whether `follow_deep_link` can replay it, and the message when it
# can't. `_parse_deep_link` classifies by iterating this table's keys (via
# `_QUERY_PARAM_KINDS`), and `follow_deep_link` and the automatic scan each do a single
# lookup here instead of consulting separate dicts and a bespoke `if` that have to be
# kept in sync by hand. Adding a future kind is a one-row change.
_LINK_KINDS: dict[str, _LinkKindPolicy] = {
    "startgroup": _LinkKindPolicy(
        resolvable=True,
        followable=False,
        rejection=(
            "{url!r} is a `startgroup` link, which opens a group chooser in a real "
            "Telegram client; only `start` deep links can be followed here — drive "
            "a group flow directly with `add_bot()` instead"
        ),
    ),
    "startapp": _LinkKindPolicy(
        resolvable=True,
        followable=False,
        rejection=_unfollowable_start_rejection("opens a Mini App"),
    ),
    "startchannel": _LinkKindPolicy(
        resolvable=True,
        followable=False,
        rejection=_unfollowable_start_rejection("opens a channel chooser"),
    ),
    "startattach": _LinkKindPolicy(
        resolvable=True,
        followable=False,
        rejection=_unfollowable_start_rejection("opens the attachment-menu chooser"),
    ),
    "attach": _LinkKindPolicy(
        resolvable=True,
        followable=False,
        rejection=_unfollowable_start_rejection("opens the attachment menu"),
    ),
    "start": _LinkKindPolicy(resolvable=True, followable=True, rejection=""),
    "invite": _LinkKindPolicy(
        resolvable=False,
        followable=False,
        rejection=_unresolvable_rejection("a chat invite link"),
    ),
    "joinchat": _LinkKindPolicy(
        resolvable=False,
        followable=False,
        rejection=_unresolvable_rejection("a chat invite link"),
    ),
    "extra_path": _LinkKindPolicy(
        resolvable=False,
        followable=False,
        rejection=_unresolvable_rejection(
            "a link with extra path segments (a message link or a Mini App shortlink)"
        ),
    ),
}

# `kind` values checked as query parameters on a `t.me` / `tg://resolve` url, in the
# order they are looked for — every table entry except the path-derived ones (`invite`,
# `joinchat`, `extra_path`), which `_parse_deep_link` recognizes from the path shape
# before any query parameter is looked at.
_QUERY_PARAM_KINDS = tuple(
    kind for kind in _LINK_KINDS if kind not in ("invite", "joinchat", "extra_path")
)


def _rejection_message(url: str, deep_link: _DeepLink) -> str:
    return _LINK_KINDS[deep_link.kind].rejection.format(url=url, kind=deep_link.kind)


def _detached(value: Any) -> Any:
    """
    Copy what the caller handed a trigger, before an update carries it into the world.

    An update is mounted to the bot on the way in, and everything nested inside it is
    mounted with it — so a trigger that embeds the very object a test passed
    (``reaction=[HEART]``, ``fields={"reply_markup": MENU}``) binds that object to a bot,
    and a module-level constant stays bound for the rest of the session, no longer equal
    to the unbound copy the world keeps. The same reasoning made declared results copies
    rather than the test's own objects, so this reuses
    :func:`aiogram.test.overrides.fresh_result` — the input side of a trigger is that
    problem seen from the other end.
    """
    if isinstance(value, dict):
        return {name: _detached(item) for name, item in value.items()}
    return fresh_result(value)


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
        """
        if isinstance(chat, ChatState):
            state = chat
        else:
            chat_id = chat if isinstance(chat, int) else chat.id
            state = self.environment.world.chat(chat_id)
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
        **data: Any,
    ) -> Any:
        """Send a message as this user. ``fields`` overrides raw ``Message`` fields."""
        message = self._build_message(text=text, fields=fields)
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

    async def edit(
        self,
        message: Message,
        text: str | None = None,
        *,
        fields: dict[str, Any] | None = None,
        **data: Any,
    ) -> Any:
        """Edit a message this user sent earlier."""
        changes: dict[str, Any] = {"text": text, **_detached(fields or {})}
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
        policy = _LINK_KINDS[deep_link.kind]
        if not policy.resolvable:
            raise WorldLookupError(_rejection_message(url, deep_link))
        if deep_link.username.lower() != bot_username.lower():
            msg = f"{url!r} deep-links to @{deep_link.username}, not to this bot (@{bot_username})"
            raise WorldLookupError(msg)
        if not policy.followable:
            raise WorldLookupError(_rejection_message(url, deep_link))

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

    async def join(self, **data: Any) -> Any:
        return await self._change_membership(ChatMemberStatus.MEMBER, data)

    async def leave(self, **data: Any) -> Any:
        return await self._change_membership(ChatMemberStatus.LEFT, data)

    async def add_bot(self, **data: Any) -> Any:
        """Add the bot to this chat, producing `my_chat_member` rather than `chat_member`."""
        return await self._change_membership(ChatMemberStatus.MEMBER, data, subject=self.bot_user)

    async def remove_bot(self, **data: Any) -> Any:
        return await self._change_membership(ChatMemberStatus.LEFT, data, subject=self.bot_user)

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
            new_reaction = _detached(reaction or [])
        # The stored reactions are copied out for the same reason the incoming ones are
        # copied in: the update binds whatever it carries, and the world's own objects are
        # compared against plainly declared ones.
        old = _detached(list(chat.reactions_for(message_id).get(self.user.id, [])))
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
        values.update(_detached(fields or {}))
        return Message(**values)

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
            f"callback_data={callback_data!r}"
        )
        raise WorldLookupError(msg)

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
            if deep_link is None or deep_link.username.lower() != bot_username.lower():
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
        Parse a `t.me` / `tg://resolve` url into a bot username, kind and start payload.

        Recognizes ``https://t.me/<username>[?start=<payload>]`` (also ``http://`` and
        schemeless ``t.me/...``) and ``tg://resolve?domain=<username>[&start=<payload>]``,
        with no path beyond the username — a bare profile link parses as a plain start
        with no payload.

        Also recognizes, but tags as unsupported rather than silently downgrading to a
        plain start: Mini App / channel / attachment-menu launches (``startapp``,
        ``startchannel``, ``startattach``, ``attach``), chat invite links
        (``t.me/+<hash>``, ``t.me/joinchat/<hash>``), and any url with extra path
        segments beyond the username (a message link like ``t.me/<username>/42``, or a
        Mini App shortlink like ``t.me/<username>/<shortname>``). Callers reject these
        `kind`s explicitly instead of treating every recognized url as a bare `/start`.

        Returns ``None`` only for urls that are not Telegram links at all.
        """
        candidate = url if "://" in url else f"https://{url}"
        parsed = urlsplit(candidate)
        scheme = parsed.scheme.lower()
        if scheme in ("http", "https"):
            if parsed.netloc.lower() not in ("t.me", "telegram.me"):
                return None
            segments = [segment for segment in parsed.path.split("/") if segment]
            if not segments:
                return None
            first = segments[0]
            if first.startswith("+"):
                return _DeepLink(username="", kind="invite", payload="")
            if first.lower() == "joinchat":
                return _DeepLink(username="", kind="joinchat", payload="")
            if len(segments) > 1:
                return _DeepLink(username=first, kind="extra_path", payload="")
            username = first
        elif scheme == "tg":
            if parsed.netloc.lower() != "resolve":
                return None
            domains = parse_qs(parsed.query, keep_blank_values=True).get("domain")
            if not domains or not domains[0]:
                return None
            username = domains[0]
        else:
            return None

        query = parse_qs(parsed.query, keep_blank_values=True)
        for kind in _QUERY_PARAM_KINDS:
            if kind in query:
                payload = query[kind][0] if query[kind] else ""
                return _DeepLink(username=username, kind=kind, payload=payload)
        return _DeepLink(username=username, kind="start", payload="")

    @property
    def bot_user(self) -> UserState:
        return self.environment.world.bot_user

    async def _change_membership(
        self,
        status: str,
        data: dict[str, Any],
        subject: UserState | None = None,
    ) -> Any:
        """
        Change a membership, routing by whose it is.

        Telegram delivers the bot's own membership change as ``my_chat_member`` and
        everyone else's as ``chat_member``; a bot that only registers the former must not
        see the latter.
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
        new = member.as_chat_member(user, chat.type)
        event = ChatMemberUpdated(
            chat=chat.as_chat(),
            from_user=self.user.as_user(),
            date=self.environment.world.next_date(),
            old_chat_member=old,
            new_chat_member=new,
        )
        update_id = self._next_update_id()
        if target.id == self.bot_user.id:
            return await self._feed(Update(update_id=update_id, my_chat_member=event), data)
        return await self._feed(Update(update_id=update_id, chat_member=event), data)
