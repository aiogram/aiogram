from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, NoReturn, TypeAlias, cast

from aiogram.client.bot import Bot
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import TelegramMethod
from aiogram.types import Message, TelegramObject, Update

from .actors import UserActor
from .blueprint import (
    Blueprint,
    BusinessConnectionSpec,
    ChatSpec,
    CommunitySpec,
    TopicSpec,
    UserSpec,
    default_blueprint,
)
from .calls import CallLog
from .defaults import resolve_defaults
from .errors import ApiRejection, WaitTimeoutError, raise_api_error
from .modeling import find_handler
from .mounting import bindables, detached_copy
from .overrides import (
    BLOCKED_BY_USER,
    OverrideBuilder,
    OverrideHandle,
    OverrideRegistry,
    block_chat,
)
from .session import FakeTelegramSession
from .synthesis import SynthesisContext, synthesize_result
from .waiting import DEFAULT_WAIT_TIMEOUT, describe_callable, poll_until
from .world import (
    BusinessConnectionState,
    ChatState,
    CommunityState,
    TopicState,
    WorldLookupError,
    describe_message,
    newest_match,
    resolve_topic,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from aiogram.methods.base import TelegramType

#: Update fields that carry a message living in a chat, in the order a single update could
#: plausibly fill them — an update carries exactly one event, so the first hit is the one.
_CARRIED_MESSAGE_FIELDS: tuple[str, ...] = (
    "message",
    "edited_message",
    "channel_post",
    "edited_channel_post",
    "business_message",
    "edited_business_message",
)

#: A chat or a topic a wait may be told to dump when it gives up. Both render themselves
#: with ``describe_messages()`` and name themselves with ``label``.
MessageView: TypeAlias = "ChatState | TopicState"

#: What :meth:`BotTestEnvironment.wait_for_message_in` accepts as "these chats".
ChatSelector: TypeAlias = "ChatSpec | ChatState | int"


@dataclass
class RouteRecord:
    """
    Where one fed update actually went — see :attr:`BotTestEnvironment.last_route`.

    The gap this closes is the one that makes a routing mistake unreadable. A dispatcher
    answers a *result*, not a route: an update swallowed by a middleware, one that matched
    a catch-all logging handler, and one that reached the handler under test all come back
    from ``feed`` as an ordinary value, and the test only notices minutes later, as a
    ``wait_for`` that timed out with nothing to say about why. This says who ran.

    ``exception`` is captured **where it was raised**, not where it surfaced. aiogram's own
    :class:`~aiogram.dispatcher.middlewares.error.ErrorsMiddleware` sits outside every
    middleware an environment can install, so a bot with an error handler swallows handler
    exceptions before any test-visible boundary sees them — the update reports itself as
    handled and the assertion fails on the missing reply instead of the real traceback.
    """

    #: ``update_id`` of the update this describes.
    update_id: int
    #: ``message``, ``callback_query``, … — the field the update actually carried, or
    #: ``None`` for an update of a type this aiogram does not know.
    event_type: str | None = None
    #: Whether the dispatcher considers the update handled — the same thing aiogram's own
    #: ``Update id=… is handled`` log line reports, which is "something other than
    #: ``UNHANDLED`` came back". A middleware that returns ``None`` instead of calling the
    #: handler therefore counts as handled here as it does there, and :attr:`handler` is
    #: the field that says whether a handler actually ran. ``False`` also covers an update
    #: whose handler raised: nothing completed, whatever an error handler answered
    #: further out.
    handled: bool = False
    #: Qualified name of the winning handler's callback, e.g. ``on_start``.
    handler: str | None = None
    #: Module the winning handler was defined in.
    handler_module: str | None = None
    #: ``Router.name`` of the router the winning handler is registered on.
    router: str | None = None
    #: The first exception raised inside the middleware chain or the handler, even if
    #: something further out caught it.
    exception: BaseException | None = None

    @property
    def handler_path(self) -> str | None:
        """``module.qualname`` of the winning handler, the way a traceback names it."""
        if self.handler is None:
            return None
        if self.handler_module is None:  # pragma: no cover - a function always has one
            return self.handler
        return f"{self.handler_module}.{self.handler}"

    def describe(self) -> str:
        """A few lines saying where the update went, for a failure message."""
        lines = [
            f"update id={self.update_id} ({self.event_type or 'unknown type'}) was "
            f"{'handled' if self.handled else 'NOT handled'}",
        ]
        if self.handler_path is not None:
            lines.append(f"  handler: {self.handler_path}")
            lines.append(f"  router:  {self.router}")
        if self.exception is not None:
            lines.append(
                f"  raised:  {type(self.exception).__name__}: {self.exception}",
            )
        return "\n".join(lines)


class _RouteMiddleware:
    """
    Outer update middleware that opens a :class:`RouteRecord` and closes it.

    Registered on ``dispatcher.update.outer_middleware`` at environment creation, which
    puts it **inside** the middlewares the dispatcher installs for itself — the error,
    user-context and FSM ones are registered in ``Dispatcher.__init__``, and outer
    middlewares run in registration order. Being inside the error middleware is exactly
    what lets the record see an exception the bot's own error handler goes on to swallow.

    It is removed again by :meth:`BotTestEnvironment._restore`, like every other mutation
    an environment makes to a dispatcher it does not own.
    """

    def __init__(self, environment: BotTestEnvironment) -> None:
        self.environment = environment

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        update = event if isinstance(event, Update) else None
        record = RouteRecord(
            update_id=update.update_id if update is not None else 0,
            event_type=_event_type_of(update),
        )
        self.environment._open_route(record)
        try:
            result = await handler(event, data)
        except BaseException as error:
            record.exception = error
            raise
        else:
            record.handled = result is not UNHANDLED
            return result
        finally:
            self.environment._close_route(record)


class _HandlerMiddleware:
    """
    Inner middleware that names the handler that won, on every event observer at once.

    The winning handler is only knowable from inside the observer: ``handler`` and
    ``event_router`` are put into the data dict by
    :meth:`~aiogram.dispatcher.event.telegram.TelegramEventObserver.trigger` and
    :meth:`~aiogram.dispatcher.router.Router.propagate_event`, and each level of the chain
    re-expands that dict into keyword arguments, so nothing an *outer* middleware holds
    ever sees them. An inner middleware registered on the **root** router's observer is
    resolved for handlers in every sub-router too — see
    ``TelegramEventObserver._resolve_middlewares``, which walks the handler's router chain
    up to the root — so one registration per event type covers the whole tree.

    Inner middlewares run only once filters have passed, which is the property that makes
    this the right place: if it ran, that handler is the one that claimed the update.
    """

    def __init__(self, environment: BotTestEnvironment) -> None:
        self.environment = environment

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        record = self.environment._current_route()
        if record is not None:
            callback = getattr(data.get("handler"), "callback", None)
            record.handler = getattr(callback, "__qualname__", None)
            record.handler_module = getattr(callback, "__module__", None)
            record.router = getattr(data.get("event_router"), "name", None)
        try:
            return await handler(event, data)
        except BaseException as error:
            # The deepest catch wins: this is the frame the exception was raised in, while
            # the update-level middleware only sees it after every inner one had a chance
            # to re-wrap it.
            if record is not None:
                record.exception = error
            raise


def _as_views(watch: MessageView | Iterable[MessageView] | None) -> tuple[MessageView, ...]:
    """``watch=`` takes one chat or many; a chat is not iterable, so this cannot guess wrong."""
    if watch is None:
        return ()
    if isinstance(watch, (ChatState, TopicState)):
        return (watch,)
    return tuple(watch)


def _describe_view(view: MessageView) -> str:
    return f"In {view.label}: {view.describe_messages()}"


def _running_tasks() -> frozenset[asyncio.Task[Any]]:
    """
    Every task alive right now, or nothing at all outside a running loop.

    The snapshot :meth:`BotTestEnvironment.drain` subtracts, so a session-scoped fixture's
    worker is not mistaken for this test's litter. The ``bot_env`` fixture is synchronous
    and therefore builds environments with no loop running at all, which is not an error
    here — it only means the snapshot is empty and ``drain`` is as blunt as it can be.
    """
    try:
        return frozenset(asyncio.all_tasks())
    except RuntimeError:
        return frozenset()


def _event_type_of(update: Update | None) -> str | None:
    """The update's event field name, or ``None`` when this aiogram cannot tell."""
    if update is None:  # pragma: no cover - the update observer only ever sees updates
        return None
    try:
        return update.event_type
    except Exception:
        # An update from a newer Bot API than this aiogram knows. `_listen_update` warns
        # and skips it; diagnostics must not be the thing that raises instead.
        return None


class BotTestEnvironment:
    """
    One isolated fake Telegram world plus the framework objects under test.

    Built from a :class:`~aiogram.test.blueprint.Blueprint`; every environment owns its
    own world, call log and overrides, so nothing is shared between tests even when the
    blueprint and the dispatcher are.
    """

    def __init__(
        self,
        blueprint: Blueprint | None = None,
        dispatcher: Dispatcher | None = None,
        *,
        default_wait_timeout: float = DEFAULT_WAIT_TIMEOUT,
    ) -> None:
        """
        ``default_wait_timeout`` is how long every wait in this environment runs.

        It is the default for :meth:`wait_for` and for
        :meth:`aiogram.test.world.ChatState.wait_for_message` and its topic-scoped twin
        alike — a bot whose background work is slow, or a suite that wants a fast failure
        instead of a five-second pause per timing bug, says so once here rather than on
        every call. It is stored on the world, which is how a chat reaches it; an explicit
        ``timeout=`` on a single call still wins over it.
        """
        self.blueprint = blueprint if blueprint is not None else default_blueprint()
        self.world = self.blueprint.build()
        self.world.default_wait_timeout = default_wait_timeout
        self.session = FakeTelegramSession(self)
        self.bot = Bot(
            token=self.blueprint.token,
            session=self.session,
            default=self.blueprint.default,
        )
        self.bot._me = self.world.bot_user.as_user()
        # From here on everything the world stores is bound to this bot, so a message a
        # test reads out of a chat is as usable as one a call returned.
        self.world.bind(self.bot)
        self.calls = CallLog()
        self.overrides = OverrideRegistry()

        self.dispatcher = dispatcher if dispatcher is not None else Dispatcher()
        self._storage = MemoryStorage()
        self._original_storage = self.dispatcher.fsm.storage
        self._original_workflow_data = dict(self.dispatcher.workflow_data)
        self.dispatcher.fsm.storage = self._storage
        self._disposed = False

        self._route_stack: list[RouteRecord] = []
        self._last_route: RouteRecord | None = None
        self._route_middleware = _RouteMiddleware(self)
        self._handler_middleware = _HandlerMiddleware(self)
        self._instrument_routing()
        self._tasks_at_creation = _running_tasks()

    # -- lifecycle --------------------------------------------------------------------

    async def dispose(self) -> None:
        """Release resources and undo every mutation made to the shared dispatcher."""
        if self._disposed:
            return
        self._disposed = True
        try:
            await self._storage.close()
            await self.session.close()
        finally:
            self._restore()

    def dispose_sync(self) -> None:
        """
        Teardown from synchronous context, used by the pytest fixture.

        The storage this environment installs is always a :class:`MemoryStorage` and the
        session is fake, so neither ``close()`` does any real work — which is what lets
        teardown avoid requiring an event loop, and therefore avoid imposing an asyncio
        integration on the project under test.
        """
        if self._disposed:
            return
        self._disposed = True
        self.session.closed = True
        self._restore()

    def _restore(self) -> None:
        self.dispatcher.fsm.storage = self._original_storage
        self.dispatcher.workflow_data.clear()
        self.dispatcher.workflow_data.update(self._original_workflow_data)
        self._uninstrument_routing()

    # -- routing diagnostics ----------------------------------------------------------

    def _instrument_routing(self) -> None:
        """
        Install the two middlewares that record :attr:`last_route`.

        A dispatcher may be shared — the ``bot_dispatcher`` fixture is commonly
        session-scoped over the project's real routers — so this follows the same rule the
        FSM storage and the workflow data follow: mutate it, remember what was mutated, and
        undo it in :meth:`_restore`. The update observer gets the outer middleware; every
        *other* observer gets the inner one, because the update observer's only handler is
        the dispatcher's own ``_listen_update`` and naming that as "the handler" would be
        worse than saying nothing.
        """
        self.dispatcher.update.outer_middleware.register(self._route_middleware)
        for name, observer in self.dispatcher.observers.items():
            if name != "update":
                observer.middleware.register(self._handler_middleware)

    def _uninstrument_routing(self) -> None:
        self.dispatcher.update.outer_middleware.unregister(self._route_middleware)
        for name, observer in self.dispatcher.observers.items():
            if name != "update":
                observer.middleware.unregister(self._handler_middleware)

    def _open_route(self, record: RouteRecord) -> None:
        self._route_stack.append(record)

    def _close_route(self, record: RouteRecord) -> None:
        self._route_stack.remove(record)
        self._last_route = record

    def _current_route(self) -> RouteRecord | None:
        """The innermost record still in flight — a handler may itself feed an update."""
        return self._route_stack[-1] if self._route_stack else None

    @property
    def last_route(self) -> RouteRecord | None:
        """
        Where the most recently finished update went, or ``None`` if none has.

        The answer to "the test timed out and I have no idea what ran"::

            await bot_user.send("/join")
            assert bot_env.last_route.handled, bot_env.last_route.describe()

        Records are completed innermost first, so after a handler that fed an update of its
        own this is still the outer update's record — the one ``feed`` was called with.

        It stays ``None`` after a fed update only when the update never reached the
        recording middleware at all, which means an update-level outer middleware
        registered on the dispatcher *before* this environment was created returned without
        calling the next one. That is itself the answer to where the update went.
        """
        return self._last_route

    def assert_handled_by(self, name: str) -> RouteRecord:
        """
        Assert that the last update was handled by a handler whose name contains ``name``.

        Matched against ``module.qualname`` as a substring, so ``"on_start"`` and
        ``"handlers.start.on_start"`` both work, and the record is returned so a test can
        go on asserting on it. The failure message is the whole point: it says where the
        update *did* go, including the exception if one was raised and swallowed.
        """
        record = self._last_route
        if record is None:
            msg = (
                f"Expected the last update to be handled by {name!r}, but no update has "
                f"been routed through this environment yet — or an update-level outer "
                f"middleware registered before the environment was created returned "
                f"without calling the next one, so nothing was recorded."
            )
            raise AssertionError(msg)
        path = record.handler_path
        if path is not None and name in path:
            return record
        msg = f"Expected the last update to be handled by {name!r}, but:\n{record.describe()}"
        raise AssertionError(msg)

    async def __aenter__(self) -> BotTestEnvironment:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.dispose()

    # -- accessors --------------------------------------------------------------------

    def user(self, user: UserSpec | int) -> UserActor:
        user_id = user.id if isinstance(user, UserSpec) else user
        return UserActor(self, self.world.user(user_id))

    def chat(self, chat: ChatSpec | int) -> ChatState:
        """
        The chat with this id, opening a declared user's private chat if that is what it is.

        An id that names a **declared user** whose private chat the blueprint did not
        mention is not an unknown chat: every Telegram user can open a private chat with a
        bot, and :meth:`aiogram.test.world.World.ensure_private_chat` already opens it for
        the actor path — ``env.user(alice).chat`` has always worked whether or not the
        blueprint declared one. This used to disagree with that: ``env.chat(alice.id)``
        raised, so the same chat was reachable through one accessor and not the other, and
        a test that had reached for it through an actor once could not name it directly.
        The asymmetry was the bug; the two now resolve the same chat.

        Every other unknown id still raises
        :class:`~aiogram.test.WorldLookupError`, because there is nothing it could
        plausibly mean: a group the blueprint never declared is a typo, not a chat the bot
        can open.
        """
        chat_id = chat.id if isinstance(chat, ChatSpec) else chat
        existing = self.world.chats.get(chat_id)
        if existing is not None:
            return existing
        if chat_id in self.world.users:
            return self.world.ensure_private_chat(chat_id)
        return self.world.chat(chat_id)

    def topic(
        self,
        chat: ChatSpec | ChatState | int,
        topic: TopicSpec | TopicState | int,
    ) -> TopicState:
        chat_state = chat if isinstance(chat, ChatState) else self.chat(chat)
        return resolve_topic(chat_state, topic)

    def business_connection(
        self,
        connection: BusinessConnectionSpec | BusinessConnectionState | str,
    ) -> BusinessConnectionState:
        if isinstance(connection, BusinessConnectionState):
            return connection
        connection_id = connection if isinstance(connection, str) else connection.id
        return self.world.business_connection(connection_id)

    def community(
        self,
        community: CommunitySpec | CommunityState | int,
    ) -> CommunityState:
        if isinstance(community, CommunityState):
            return community
        community_id = community if isinstance(community, int) else community.id
        return self.world.community(community_id)

    def on(self, method_type: type[TelegramMethod[Any]], **fields: Any) -> OverrideBuilder:
        """
        Declare what a Bot API call answers, optionally only for calls of a given shape.

        Without keyword arguments this is what it always was — every call of that method
        type::

            env.on(GetChatMember).returns(member)

        With them, the override is addressed: each keyword is an equality test on a field of
        the **resolved** method, and they are AND-ed. That is what makes "this one chat
        rejects us" expressible when the bot messages several chats from one trigger::

            env.on(SendMessage, chat_id=alice.id).raises(TelegramForbiddenError)
            env.on(SendMessage, chat_id=bob.id).raises(TelegramForbiddenError)

        Both rules stand at once, neither is spent by a message to the group between them,
        and neither shadows the other — a rule whose matcher rejects a call is skipped
        without its ``times`` budget moving. A field the method does not have raises
        immediately rather than registering a rule that can never match; see
        :meth:`~aiogram.test.overrides.OverrideBuilder.where` for what equality cannot say.

        The returned builder is also the handle: ``.cancel()`` withdraws exactly what it
        registered, and it works as a ``with`` block.
        """
        return OverrideBuilder(self.overrides, method_type, **fields)

    def blocked(
        self,
        chat_id: ChatSpec | ChatState | UserSpec | int,
        *,
        message: str = BLOCKED_BY_USER,
    ) -> OverrideHandle:
        """
        Make every delivery into one chat fail the way a block makes it fail.

        The shape of the single most common "one addressee is unreachable" test, which
        otherwise has to be spelled out one method at a time. Scoped::

            with env.blocked(chat_id=alice.id):
                await bot_user.send("/start")   # the group still gets its message

        or open-ended, cancelled by hand::

            block = env.blocked(chat_id=alice.id)
            ...
            block.cancel()

        Every method that delivers content into a chat is covered, not only
        ``sendMessage`` — the block a real user applies stops photos, copies and forwards
        just the same, and a bot that falls back from one to another must be seen to fail
        at all of them. See :data:`aiogram.test.overrides.DELIVERY_METHODS`.

        The call is still **recorded** before the block answers it, so a test can assert
        both that the bot tried and that it failed — see :meth:`handle_call`.
        """
        resolved = chat_id if isinstance(chat_id, int) else chat_id.id
        return block_chat(self.overrides, resolved, message=message)

    def state(
        self,
        user: UserSpec | int,
        chat: ChatSpec | ChatState | int | None = None,
        *,
        topic: TopicSpec | TopicState | int | None = None,
        business_connection: BusinessConnectionSpec | BusinessConnectionState | str | None = None,
    ) -> FSMContext:
        """
        FSM context for a user, resolved with the dispatcher's own strategy.

        ``topic`` and ``business_connection`` are part of the storage key under the
        topic-aware strategies and on business connections — omitting them there would
        return a context for a *different* key than the one the dispatcher used.
        """
        user_id = user.id if isinstance(user, UserSpec) else user
        if chat is None:
            chat_id = user_id
        elif isinstance(chat, ChatState):
            chat_id = chat.id
        else:
            chat_id = chat.id if isinstance(chat, ChatSpec) else chat
        thread_id: int | None = None
        if topic is not None:
            resolved_topic = self.topic(chat_id, topic)
            thread_id = resolved_topic.message_thread_id
        connection_id: str | None = None
        if business_connection is not None:
            connection_id = self.business_connection(business_connection).id
        context = self.dispatcher.fsm.resolve_context(
            bot=self.bot,
            chat_id=chat_id,
            user_id=user_id,
            thread_id=thread_id,
            business_connection_id=connection_id,
        )
        if context is None:  # pragma: no cover
            msg = "FSM is disabled on this dispatcher"
            raise RuntimeError(msg)
        return context

    async def feed(self, update: Update, **kwargs: Any) -> Any:
        """
        Run an update through the dispatcher, as this environment's bot.

        The update is mounted first, and that is load-bearing rather than tidy:
        :meth:`~aiogram.dispatcher.dispatcher.Dispatcher.feed_update` re-mounts an update
        that carries a different bot by dumping it to JSON and validating it again, which
        mints copies of everything inside. A handler would then receive a *twin* of the
        message the chat stores, so ``message is bot_chat.messages[-1]`` would be false and
        an edit applied through the handler's object would land on an orphan. Arriving
        already mounted skips that round-trip: handlers work on the world's own objects.

        There are three cases, and one walk tells them apart. An update built by an actor is
        **this environment's** and is mounted in place, because that identity is the whole
        point. An update a test constructed by hand is **unbound**, and the same pass claims
        it. An update carrying objects that belong to **another** environment cannot be
        claimed at all: :func:`~aiogram.test.mounting.mount` stops at anything already bound,
        so a module-level update fed to two environments would keep the first one's bot and
        every reply the second one's handlers send would land in the first one's world —
        silently, since two bots built from one blueprint compare equal. Such an update is
        copied, and the copy is this environment's.

        Whatever the case, the message the update carries ends up **registered in its chat**
        — see :meth:`_register_carried_message`.
        """
        # One pass over the bindables instead of one to ask whose they are and another to
        # claim them: `bound_elsewhere` and `mount` walk the same graph with the same
        # pruning, and an update is walked on every single trigger.
        nodes = list(bindables(update, prune_bound=True))
        if any(node.bot is not None and node.bot is not self.bot for node in nodes):
            update = detached_copy(update, bot=self.bot)
        else:
            for node in nodes:
                if node.bot is None:
                    node.as_(self.bot)
        self._register_carried_message(update)
        # Cleared rather than left standing, so `last_route` is never a *previous* update's
        # route mistaken for this one's — the case that happens exactly when an outer
        # middleware the dispatcher already had swallows the update before the recorder.
        self._last_route = None
        return await self.dispatcher.feed_update(self.bot, update, **kwargs)

    def _register_carried_message(self, update: Update) -> None:
        """
        Let the destination chat know about a message arriving from outside it.

        An actor puts its message in the chat and *then* builds the update around it, so
        there is normally nothing to do here — the message is found by id and left alone,
        which is what keeps ``message is chat.messages[-1]`` true. The case this exists for
        is the update that did not come from this world: the two-environment recipe in the
        documentation feeds one environment an update the other one built, and the copy that
        makes is a message no chat here has ever seen. Without registering it, the chat's
        allocator is still behind — so the bot's first reply is minted with the *same*
        ``message_id`` as the incoming message, and the next edit hits whichever of the two
        ``find_message`` reaches first.

        Storing it is also simply what Telegram does: a message the bot is told about is in
        the chat, and a test that goes on to assert on ``chat.messages`` should see it.

        The id such a message carries was allocated in the *other* world, so it may be older
        than what this chat already holds — which is why
        :meth:`aiogram.test.world.ChatState.add_message` places a message by id rather than
        appending it. Registering an id 50 into a chat whose last message is 101 must not
        leave ``chat.messages[-1]`` pointing at the carried message.

        **A collision is loud, not silent.** If the id is already taken by a message that is
        genuinely different, keeping the old one and dropping the incoming one would leave a
        handler processing a message the world will never hold — nothing it does to that
        message is ever observable, and a ``wait_for_message`` waiting for it waits forever,
        with no clue why. So this raises :class:`~aiogram.test.world.WorldLookupError` naming
        both messages, rather than picking one silently. It does not raise on a re-feed of an
        update that is already registered, or of an equal one built the same way twice: by
        the time this runs the incoming message is bound to this environment's bot, same as
        anything already stored, so comparing equal is exactly what "the same message, again"
        means, and that case stays the silent no-op it always was.
        """
        for name in _CARRIED_MESSAGE_FIELDS:
            message: Message | None = getattr(update, name, None)
            if message is None:
                continue
            chat = self.world.chats.get(message.chat.id)
            if chat is None:
                # Not a chat this world declared; nothing to keep it in.
                return
            existing = chat.find_message(message.message_id)
            if existing is None:
                chat.add_message(message)
            elif existing != message:
                msg = (
                    f"Chat {chat.id} already holds a different message under id "
                    f"{message.message_id}, so the incoming one cannot be registered:\n"
                    f"  already there: {describe_message(existing)}\n"
                    f"  incoming:      {describe_message(message)}\n"
                    "A handler that reacts to the incoming update would be working on a "
                    "message this world never stores, and a wait_for_message waiting for it "
                    "would wait forever. Feed updates whose message ids the destination "
                    "environment has not already used, or let the toolkit allocate the id "
                    "instead of carrying one minted by another environment."
                )
                raise WorldLookupError(msg)
            # Even an already-known message may have been allocated elsewhere.
            chat.last_message_id = max(chat.last_message_id, message.message_id)
            return

    # -- waiting ----------------------------------------------------------------------

    async def wait_for(
        self,
        predicate: Callable[[], object],
        description: str | None = None,
        *,
        watch: MessageView | Iterable[MessageView] | None = None,
        timeout: float | None = None,
        interval: float = 0.01,
    ) -> Any:
        """
        Wait until ``predicate`` returns something truthy, and return that value.

        A bot that runs an engine of its own — background tasks, timers, a scheduler —
        changes the world after the trigger returns, while every assertion on the world is
        an instant snapshot. This is the poller for that gap: it re-checks ``predicate``
        every ``interval`` seconds, yielding to the event loop in between so those tasks
        get to run.

        ``predicate`` takes no arguments and may be synchronous or return an awaitable.
        Whatever it returns is handed back, so it can both test and fetch::

            await bot_env.wait_for(lambda: game.phase is Phase.NIGHT)
            victim = await bot_env.wait_for(lambda: game.find_victim())

        It is checked immediately before any sleeping, so an already-satisfied wait is
        free, and once more after the deadline passes, so a change landing exactly on the
        deadline still counts.

        ``description`` names the condition in the failure message; without it the
        message can only identify the predicate itself, which for a lambda is not much.
        Since a lambda is what this is written with, it is the second **positional**
        parameter, so saying what is awaited costs no ceremony::

            await bot_env.wait_for(lambda: game.phase is Phase.NIGHT, "night to fall")

        ``timeout`` defaults to this environment's ``default_wait_timeout``, set once when
        the environment is built; passing one here wins over it for this call.

        ``watch`` names the chats or topics whose contents to dump if the wait fails. A
        general ``wait_for`` can only report the condition it was given, and the condition
        is a lambda over the bot's own state — while the answer to "why did it never become
        true" is almost always in what the bot said instead::

            await bot_env.wait_for(lambda: game.phase is Phase.NIGHT, "night", watch=group)

        A single chat or topic, or any iterable of them, and each is appended to the failure
        message the way :meth:`aiogram.test.world.ChatState.wait_for_message` already
        renders one.

        :raises aiogram.test.errors.WaitTimeoutError: if the condition never became true.
        """
        if timeout is None:
            timeout = self.world.default_wait_timeout
        watched = _as_views(watch)

        def describe_timeout() -> str:
            if description is not None:
                head = f"Timed out after {timeout}s waiting for {description}."
            else:
                head = (
                    f"Timed out after {timeout}s waiting for predicate "
                    f"{describe_callable(predicate)} to return a truthy value. Pass "
                    f"`description='...'` to say what was expected — it is the only thing "
                    f"this message can show about a lambda."
                )
            return "\n".join([head, *(_describe_view(view) for view in watched)])

        return await poll_until(
            predicate,
            timeout=timeout,
            interval=interval,
            describe_timeout=describe_timeout,
        )

    async def wait_for_message_in(
        self,
        chats: Iterable[ChatSelector],
        predicate: Callable[[Message], object] | None = None,
        description: str | None = None,
        *,
        timeout: float | None = None,
        interval: float = 0.01,
    ) -> dict[int, Message]:
        """
        Wait until **every** one of ``chats`` holds a matching message, and return them.

        The broadcast wait. A bot that fans one event out to many chats — every player gets
        the night keyboard, every subscriber gets the digest — is otherwise tested by
        awaiting each chat in turn, which is both slower (the timeouts are serial) and much
        worse at failing: the first chat that never got its message ends the wait, and the
        other nine are never even looked at, so a systematic failure reads as a single
        unlucky chat.

        This polls all of them together and returns ``chat_id -> message`` once all match,
        taking the **newest** match per chat, as
        :meth:`aiogram.test.world.ChatState.wait_for_message` does::

            keyboards = await bot_env.wait_for_message_in(
                players, lambda m: m.reply_markup is not None, "the night keyboard"
            )

        ``chats`` accepts declarations, chat states and bare ids, mixed. A predicate that
        raises on a message counts as "no match" for that message, again as the single-chat
        wait has it: a chat holds messages of every shape and a wait has no business dying
        on one it was not asking about.

        The failure names **which** chats are still missing one and dumps only those,
        which is the difference between "somebody did not get it" and a readable diagnosis.

        :raises aiogram.test.errors.WaitTimeoutError: if some chat never got a match.
        """
        if timeout is None:
            timeout = self.world.default_wait_timeout
        states = [chat if isinstance(chat, ChatState) else self.chat(chat) for chat in chats]

        def collect() -> dict[int, Message] | None:
            found: dict[int, Message] = {}
            for state in states:
                match = newest_match(state.messages, predicate)
                if match is None:
                    return None
                found[state.id] = match
            return found

        def describe_timeout() -> str:
            missing = [
                state for state in states if newest_match(state.messages, predicate) is None
            ]
            what = description or (
                "any message"
                if predicate is None
                else f"a message matching {describe_callable(predicate)}"
            )
            head = (
                f"Timed out after {timeout}s waiting for {what} in all "
                f"{len(states)} watched chat(s). Still missing in "
                f"{', '.join(str(state.id) for state in missing)}:"
            )
            return "\n".join([head, *(_describe_view(state) for state in missing)])

        return cast(
            "dict[int, Message]",
            await poll_until(
                collect,
                timeout=timeout,
                interval=interval,
                describe_timeout=describe_timeout,
            ),
        )

    async def drain(self, timeout: float = 1.0) -> int:
        """
        Cancel and await the tasks this test left running, and report how many there were.

        Opt-in, and deliberately not part of teardown. A bot with an engine of its own
        spawns fire-and-forget tasks — ``asyncio.create_task(self._night_timer())`` — and
        the test ends while they are still sleeping. The loop is then torn down under them,
        and every one of them prints ``Task was destroyed but it is pending!`` to stderr
        after the test that caused it has already passed, which is noise nobody can trace
        back. Awaiting the cancellations here turns that into nothing at all::

            await bot_env.drain()

        Tasks that were already running when the environment was built are left alone: a
        session-scoped fixture's background worker is not this test's litter. If the
        environment was built outside a running loop — which the ``bot_env`` fixture does,
        being synchronous — there was nothing to snapshot, and every task alive at the
        moment of the call except the caller's own is treated as this test's.

        **It is not called by** :meth:`dispose` **or** :meth:`dispose_sync`. Two reasons,
        and the second is the real one: ``dispose_sync`` is what the pytest fixture uses and
        cannot await anything at all, so auto-draining would work in one teardown path and
        silently not in the other. And cancelling tasks a test never mentioned, as an
        invisible side effect of a fixture going out of scope, turns "my bot's scheduler
        stopped" into a mystery. A test that wants its tasks gone says so.

        :raises aiogram.test.errors.WaitTimeoutError: if a task refuses to finish within
            ``timeout`` after being cancelled — a task that swallows
            :class:`asyncio.CancelledError` is a real bug in the bot, and silently leaving
            it running would be the same stderr noise this exists to remove.
        """
        current = asyncio.current_task()
        pending = {
            task
            for task in asyncio.all_tasks()
            if task is not current and task not in self._tasks_at_creation and not task.done()
        }
        if not pending:
            return 0
        for task in pending:
            task.cancel()
        _, still_running = await asyncio.wait(pending, timeout=timeout)
        for task in pending - still_running:
            # Retrieve whatever the task ended with, or asyncio complains about the
            # never-retrieved exception at collection time — the very noise being removed.
            if not task.cancelled():
                task.exception()
        if still_running:
            names = ", ".join(sorted(task.get_name() for task in still_running))
            msg = (
                f"{len(still_running)} task(s) were still running {timeout}s after being "
                f"cancelled: {names}.\n"
                f"A task that outlives its cancellation is swallowing CancelledError — "
                f"look for a bare `except Exception` or a `finally` that awaits."
            )
            raise WaitTimeoutError(msg)
        return len(pending)

    # -- call handling ----------------------------------------------------------------

    def synthesis_context(self) -> SynthesisContext:
        return SynthesisContext(
            chat=None,
            user=self.world.bot_user.as_user(),
            date=self.world.next_date(),
            counter=self.world.last_update_id,
        )

    def fail(
        self,
        method: TelegramMethod[Any],
        description: str,
        error_code: int = HTTPStatus.BAD_REQUEST,
    ) -> NoReturn:
        raise_api_error(
            session=self.session,
            bot=self.bot,
            method=method,
            description=description,
            error_code=error_code,
        )

    async def handle_call(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Any:
        """
        Override, then model, then synthesize — see design decision D3.

        This is also the toolkit's **copy-in choke point**. The call log records the object
        the caller actually built, and everything downstream gets a
        :func:`~aiogram.test.mounting.detached_copy` of it — so a handler may store whatever
        it reads off the method without a copy of its own, and the test's module-level
        ``reply_markup`` constant never ends up *in* the world, bound to a bot and no longer
        equal to its unbound twin. Doing it once here rather than per handler is what makes
        the rule impossible for the next handler to forget; see the module docstring of
        :mod:`aiogram.test.modeling` for the boundary as a whole.

        **The call is recorded before overrides are consulted**, and that ordering is a
        feature rather than an accident of the code. An override — a rate limit, a
        `TelegramForbiddenError` from :meth:`blocked` — models the *API refusing*, and a
        refused call is still a call the bot made. Recording it first is what lets a test
        assert the two halves separately: that the bot addressed the right chat with the
        right text, and that it coped with the refusal. Recording after would erase the
        first half exactly when it matters most, since the refusal path is the one where
        "did we even try, and try at whom?" is the question.

        A modeled rejection comes back as the :class:`~aiogram.exceptions.TelegramBadRequest`
        Telegram would have answered with. A :class:`~aiogram.test.WorldLookupError`
        deliberately does **not**: a gap in the test's own setup must fail the test rather
        than arrive as an error the bot under test can catch.
        """
        resolved = resolve_defaults(method, bot)
        self.calls.record(resolved)
        resolved = detached_copy(resolved)

        outcome = self.overrides.take(resolved)
        if outcome is not None:
            # The destination is known here, so the copy is minted already bound and the
            # session's `mount` prunes at its root instead of walking it again.
            return outcome.apply(resolved, bot)

        handler = find_handler(resolved)
        if handler is not None:
            try:
                return handler(self, resolved)
            except ApiRejection as error:
                self.fail(resolved, f"Bad Request: {error}")

        return synthesize_result(resolved.__returning__, self.synthesis_context())


def build_environment(
    blueprint: Blueprint | None = None,
    dispatcher: Dispatcher | None = None,
) -> BotTestEnvironment:
    """Convenience constructor mirroring the fixture, for use outside pytest."""
    return BotTestEnvironment(blueprint=blueprint, dispatcher=dispatcher)
