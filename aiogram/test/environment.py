from __future__ import annotations

from collections.abc import Callable
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, NoReturn

from aiogram.client.bot import Bot
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import TelegramMethod
from aiogram.types import Update

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
from .errors import raise_api_error
from .modeling import find_handler
from .mounting import bound_elsewhere, detached_copy, mount
from .overrides import OverrideBuilder, OverrideRegistry
from .session import FakeTelegramSession
from .synthesis import SynthesisContext, synthesize_result
from .waiting import describe_callable, poll_until
from .world import (
    BusinessConnectionState,
    ChatState,
    CommunityState,
    TopicState,
    WorldLookupError,
    resolve_topic,
)

if TYPE_CHECKING:
    from aiogram.methods.base import TelegramType


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
    ) -> None:
        self.blueprint = blueprint if blueprint is not None else default_blueprint()
        self.world = self.blueprint.build()
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

    async def __aenter__(self) -> BotTestEnvironment:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.dispose()

    # -- accessors --------------------------------------------------------------------

    def user(self, user: UserSpec | int) -> UserActor:
        user_id = user.id if isinstance(user, UserSpec) else user
        return UserActor(self, self.world.user(user_id))

    def chat(self, chat: ChatSpec | int) -> ChatState:
        chat_id = chat.id if isinstance(chat, ChatSpec) else chat
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

    def on(self, method_type: type[TelegramMethod[Any]]) -> OverrideBuilder:
        return OverrideBuilder(self.overrides, method_type)

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

        An update built by an actor is mounted in place, because that identity is the whole
        point. An update carrying objects that belong to *another* environment cannot be:
        :func:`~aiogram.test.mounting.mount` stops at anything already bound, so a
        module-level update fed to two environments would keep the first one's bot and every
        reply the second one's handlers send would land in the first one's world — silently,
        since two bots built from one blueprint compare equal. Such an update is copied
        first, and the copy is this environment's.
        """
        if bound_elsewhere(update, self.bot):
            update = detached_copy(update, bot=self.bot)
        mount(update, self.bot)
        return await self.dispatcher.feed_update(self.bot, update, **kwargs)

    # -- waiting ----------------------------------------------------------------------

    async def wait_for(
        self,
        predicate: Callable[[], object],
        *,
        timeout: float = 5.0,
        interval: float = 0.01,
        description: str | None = None,
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

        :raises aiogram.test.errors.WaitTimeoutError: if the condition never became true.
        """

        def describe_timeout() -> str:
            if description is not None:
                return f"Timed out after {timeout}s waiting for {description}."
            return (
                f"Timed out after {timeout}s waiting for predicate "
                f"{describe_callable(predicate)} to return a truthy value. Pass "
                f"`description='...'` to say what was expected — it is the only thing "
                f"this message can show about a lambda."
            )

        return await poll_until(
            predicate,
            timeout=timeout,
            interval=interval,
            describe_timeout=describe_timeout,
        )

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
        """Override, then model, then synthesize — see design decision D3."""
        resolved = resolve_defaults(method, bot)
        self.calls.record(resolved)

        outcome = self.overrides.take(resolved)
        if outcome is not None:
            # The destination is known here, so the copy is minted already bound and the
            # session's `mount` prunes at its root instead of walking it again.
            return outcome.apply(resolved, bot)

        handler = find_handler(resolved)
        if handler is not None:
            try:
                return handler(self, resolved)
            except WorldLookupError as error:
                self.fail(resolved, f"Bad Request: {error}")

        return synthesize_result(resolved.__returning__, self.synthesis_context())


def build_environment(
    blueprint: Blueprint | None = None,
    dispatcher: Dispatcher | None = None,
) -> BotTestEnvironment:
    """Convenience constructor mirroring the fixture, for use outside pytest."""
    return BotTestEnvironment(blueprint=blueprint, dispatcher=dispatcher)
