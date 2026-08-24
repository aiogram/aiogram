from __future__ import annotations

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
from .overrides import OverrideBuilder, OverrideRegistry
from .session import FakeTelegramSession
from .synthesis import SynthesisContext, synthesize_result
from .world import (
    BusinessConnectionState,
    ChatState,
    CommunityState,
    TopicState,
    WorldLookupError,
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
        if isinstance(topic, TopicState):
            return topic
        thread_id = topic if isinstance(topic, int) else topic.message_thread_id
        return chat_state.topic(thread_id)

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
        return await self.dispatcher.feed_update(self.bot, update, **kwargs)

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
            return outcome.apply(resolved)

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
