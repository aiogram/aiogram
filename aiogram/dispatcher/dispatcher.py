from __future__ import annotations

import asyncio
import contextvars
import signal
import warnings
from asyncio import CancelledError, Event, Future, Lock
from collections.abc import AsyncGenerator, Awaitable
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from aiogram import loggers
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.middleware import FSMContextMiddleware
from aiogram.fsm.storage.base import BaseEventIsolation, BaseStorage
from aiogram.fsm.storage.memory import DisabledEventIsolation, MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.methods import GetUpdates, TelegramMethod
from aiogram.types import ErrorEvent, Update, User
from aiogram.types.base import UNSET, UNSET_TYPE
from aiogram.types.update import UpdateTypeLookupError
from aiogram.utils.backoff import Backoff, BackoffConfig

from .event.bases import UNHANDLED, SkipHandler
from .event.telegram import TelegramEventObserver
from .middlewares.error import ErrorsMiddleware
from .middlewares.user_context import UserContextMiddleware
from .router import Router
from .table import DispatchTable, HandlerResultHook, compile_table, execute, route_update

if TYPE_CHECKING:
    from aiogram.client.bot import Bot
    from aiogram.methods.base import TelegramType

DEFAULT_BACKOFF_CONFIG = BackoffConfig(min_delay=1.0, max_delay=5.0, factor=1.3, jitter=0.1)


def _set_log_context(bot_id: int, update: Update) -> contextvars.Token[loggers.LogContext | None]:
    try:
        update_type: str | None = update.event_type
    except UpdateTypeLookupError:
        update_type = None
    return loggers._current.set(loggers.LogContext(bot_id, update.update_id, update_type))


class Dispatcher(Router):
    """
    Root router
    """

    def __init__(
        self,
        *,  # * - Preventing to pass instance of Bot to the FSM storage
        storage: BaseStorage | None = None,
        fsm_strategy: FSMStrategy = FSMStrategy.USER_IN_CHAT,
        events_isolation: BaseEventIsolation | None = None,
        disable_fsm: bool = False,
        fsm_key_on_sender_chat: bool = False,
        name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Root router

        :param storage: Storage for FSM
        :param fsm_strategy: FSM strategy
        :param events_isolation: Events isolation
        :param disable_fsm: Disable FSM, note that if you disable FSM
            then you should not use storage and events isolation
        :param fsm_key_on_sender_chat: Use :code:`sender_chat.id` as the user id of the FSM key
            for messages sent on behalf of a chat in non-channel chats
            (anonymous group administrators, users posting as a channel)
        :param kwargs: Other arguments, will be passed as keyword arguments to handlers
        """
        super().__init__(name=name)

        if storage and not isinstance(storage, BaseStorage):
            msg = f"FSM storage should be instance of 'BaseStorage' not {type(storage).__name__}"
            raise TypeError(msg)

        # Telegram API provides originally only one event type - Update
        # For making easily interactions with events here is registered handler which helps
        # to separate Update to different event types like Message, CallbackQuery etc.
        self.update = self.observers["update"] = TelegramEventObserver(
            router=self,
            event_name="update",
        )
        self.update.register(self._listen_update)

        # Error handlers should work is out of all other functions
        # and should be registered before all others middlewares
        self.update.outer_middleware(ErrorsMiddleware(self))

        # User context middleware makes small optimization for all other builtin
        # middlewares via caching the user and chat instances in the event context
        self.update.outer_middleware(UserContextMiddleware())

        # FSM middleware should always be registered after User context middleware
        # because here is used context from previous step
        self.fsm = FSMContextMiddleware(
            storage=storage or MemoryStorage(),
            strategy=fsm_strategy,
            events_isolation=events_isolation or DisabledEventIsolation(),
            key_on_sender_chat=fsm_key_on_sender_chat,
        )
        if not disable_fsm:
            # Note that when FSM middleware is disabled, the event isolation is also disabled
            # Because the isolation mechanism is a part of the FSM
            self.update.outer_middleware(self.fsm)
        self.shutdown.register(self.fsm.close)

        self.workflow_data: dict[str, Any] = kwargs
        self._running_lock = Lock()
        self._stop_signal: Event | None = None
        self._stopped_signal: Event | None = None
        self._handle_update_tasks: set[asyncio.Task[Any]] = set()
        # Called with each handler's return value inside its middleware scope (see table.py)
        self._on_handler_result: HandlerResultHook | None = None
        # A precompiled table feed_update uses instead of compiling one per update (benchmarks);
        # the routing snapshot lifecycle replaces it with a cache
        self._table: DispatchTable | None = None

    def __getitem__(self, item: str) -> Any:
        return self.workflow_data[item]

    def get(self, key: str, /, default: Any | None = None) -> Any | None:
        return self.workflow_data.get(key, default)

    @property
    def storage(self) -> BaseStorage:
        return self.fsm.storage

    @property
    def parent_router(self) -> Router | None:
        """
        Dispatcher has no parent router and can't be included to any other routers or dispatchers

        :return:
        """
        return None

    @parent_router.setter
    def parent_router(self, value: Router) -> None:
        """
        Dispatcher is root Router then configuring parent router is not allowed

        :param value:
        :return:
        """
        msg = "Dispatcher can not be attached to another Router."
        raise RuntimeError(msg)

    async def feed_update(self, bot: Bot, update: Update, **kwargs: Any) -> Any:
        """
        Main entry point for incoming updates
        Response of this method can be used as Webhook response

        :param bot:
        :param update:
        """
        bot_id = bot.id
        # The log context covers the whole call, the final "handled" record included;
        # a nested feed_update restores the outer context on reset.
        log_token = _set_log_context(bot_id, update)
        try:
            loop = asyncio.get_running_loop()
            handled = False
            start_time = loop.time()

            if update.bot != bot:
                # Re-mounting update to the current bot instance for making possible to
                # use it in shortcuts.
                # Here is update is re-created because we need to propagate context to
                # all nested objects and attributes of the Update, but it
                # is impossible without roundtrip to JSON :(
                # The preferred way is that pass already mounted Bot instance to this update
                # before call feed_update method
                update = Update.model_validate(update.model_dump(), context={"bot": bot})

            try:
                table = self._table or compile_table(
                    self, on_handler_result=self._on_handler_result
                )
                response = await execute(table, bot, update, kwargs)
                handled = response is not UNHANDLED
                return response
            finally:
                finish_time = loop.time()
                duration = (finish_time - start_time) * 1000
                loggers.event.info(
                    "Update id=%s is %s. Duration %d ms by bot id=%d",
                    update.update_id,
                    "handled" if handled else "not handled",
                    duration,
                    bot_id,
                )
        finally:
            loggers._current.reset(log_token)

    async def feed_raw_update(self, bot: Bot, update: dict[str, Any], **kwargs: Any) -> Any:
        """
        Main entry point for incoming updates with automatic Dict->Update serializer

        :param bot:
        :param update:
        :param kwargs:
        """
        parsed_update = await self._validate_update(bot, update, **kwargs)
        if parsed_update is None:
            return UNHANDLED
        return await self._feed_webhook_update(bot=bot, update=parsed_update, **kwargs)

    async def _validate_update(self, bot: Bot, update: Any, **kwargs: Any) -> Update | None:
        """
        Validate a raw update, or skip it when it can't be validated.

        Telegram would redeliver such an update forever, so it is dropped: logged with the
        error count only (rendering every error of a large update blocks the event loop)
        and reported to the ``errors`` observers as an :class:`ErrorEvent` whose update
        carries only ``update_id``. Delivery is best-effort: the update is lost.
        """
        try:
            return Update.model_validate(update, context={"bot": bot})
        except ValidationError as e:
            # Handled outside the except block, so that nothing raised later is chained to it
            error = e

        update_id = update.get("update_id") if isinstance(update, dict) else None
        if type(update_id) is not int:
            update_id = None
        # The skip records belong to this update, which never reaches feed_update
        log_token = loggers._current.set(loggers.LogContext(bot.id, update_id, None))
        try:
            first = error.errors(include_url=False, include_context=False, include_input=False)[0]
            loggers.webhook.error(
                "Update id=%s is skipped because it can't be validated by bot id=%d: "
                "%d validation errors, first: %s at %s",
                update_id,
                bot.id,
                error.error_count(),
                first["type"],
                first["loc"],
            )
            loggers.webhook.debug("Skipped update: %r", update)
            if update_id is None:
                return None

            try:
                await self.propagate_event(
                    update_type="error",
                    event=ErrorEvent(update=Update(update_id=update_id), exception=error),
                    **{"dispatcher": self, **self.workflow_data, **kwargs, "bot": bot},
                )
            except Exception:  # noqa: BLE001
                # The update is skipped anyway: a failing error handler must not turn it into
                # a non-2xx answer that makes Telegram redeliver it
                loggers.event.exception(
                    "Error handler failed for skipped update id=%d by bot id=%d",
                    update_id,
                    bot.id,
                )
            return None
        finally:
            loggers._current.reset(log_token)

    @classmethod
    async def _listen_updates(
        cls,
        bot: Bot,
        polling_timeout: int = 30,
        backoff_config: BackoffConfig = DEFAULT_BACKOFF_CONFIG,
        allowed_updates: list[str] | None = None,
    ) -> AsyncGenerator[Update, None]:
        """
        Endless updates reader with correctly handling any server-side or connection errors.

        So you may not worry that the polling will stop working.
        """
        backoff = Backoff(config=backoff_config)
        get_updates = GetUpdates(timeout=polling_timeout, allowed_updates=allowed_updates)
        kwargs = {}
        if bot.session.timeout:
            # Request timeout can be lower than session timeout and that's OK.
            # To prevent false-positive TimeoutError we should wait longer than polling timeout
            kwargs["request_timeout"] = int(bot.session.timeout + polling_timeout)
        failed = False
        while True:
            try:
                updates = await bot(get_updates, **kwargs)
            except Exception as e:  # noqa: BLE001
                failed = True
                # In cases when Telegram Bot API was inaccessible don't need to stop polling
                # process because some developers can't make auto-restarting of the script
                loggers.dispatcher.error("Failed to fetch updates - %s: %s", type(e).__name__, e)
                # And also backoff timeout is best practice to retry any network activity
                loggers.dispatcher.warning(
                    "Sleep for %f seconds and try again... (tryings = %d, bot id = %d)",
                    backoff.next_delay,
                    backoff.counter,
                    bot.id,
                )
                await backoff.asleep()
                continue

            # In case when network connection was fixed let's reset the backoff
            # to initial value and then process updates
            if failed:
                loggers.dispatcher.info(
                    "Connection established (tryings = %d, bot id = %d)",
                    backoff.counter,
                    bot.id,
                )
                backoff.reset()
                failed = False

            for update in updates:
                yield update
                # The getUpdates method returns the earliest 100 unconfirmed updates.
                # To confirm an update, use the offset parameter when calling getUpdates
                # All updates with update_id less than or equal to offset will be marked
                # as confirmed on the server and will no longer be returned.
                get_updates.offset = update.update_id + 1

    async def _listen_update(self, update: Update, **kwargs: Any) -> Any:
        """
        Main updates listener

        Workflow:
        - Detect content type and propagate to observers in current router
        - If no one filter is pass - propagate update to child routers as Update

        :param update:
        :param kwargs:
        :return:
        """
        table = compile_table(self, on_handler_result=self._on_handler_result)
        return await route_update(table.by_event, update, kwargs)

    @classmethod
    async def silent_call_request(cls, bot: Bot, result: TelegramMethod[Any]) -> None:
        """
        Simulate answer into WebHook

        :param bot:
        :param result:
        :return:
        """
        try:
            await bot(result)
        except TelegramAPIError as e:
            # In due to WebHook mechanism doesn't allow getting response for
            # requests called in answer to WebHook request.
            # Need to skip unsuccessful responses.
            # For debugging here is added logging.
            loggers.event.error("Failed to make answer: %s: %s", e.__class__.__name__, e)

    async def _process_update(
        self,
        bot: Bot,
        update: Update,
        call_answer: bool = True,
        **kwargs: Any,
    ) -> bool:
        """
        Propagate update to event listeners

        :param bot: instance of Bot
        :param update: instance of Update
        :param call_answer: need to execute response as Telegram method (like answer into webhook)
        :param kwargs: contextual data for middlewares, filters and handlers
        :return: status
        """
        # The error and answer records are logged after feed_update has reset its context
        log_token = _set_log_context(bot.id, update)
        try:
            response = await self.feed_update(bot, update, **kwargs)
            if call_answer and isinstance(response, TelegramMethod):
                await self.silent_call_request(bot=bot, result=response)

        except Exception as e:  # noqa: BLE001
            loggers.event.exception(
                "Cause exception while process update id=%d by bot id=%d\n%s: %s",
                update.update_id,
                bot.id,
                e.__class__.__name__,
                e,
            )
            return True  # because update was processed but unsuccessful

        else:
            return response is not UNHANDLED
        finally:
            loggers._current.reset(log_token)

    async def _process_with_semaphore(
        self,
        handle_update: Awaitable[bool],
        semaphore: asyncio.Semaphore,
    ) -> bool:
        """
        Process update with semaphore to limit concurrent tasks

        :param handle_update: Coroutine that processes the update
        :param semaphore: Semaphore to limit concurrent tasks
        :return: bool indicating the result of the update processing
        """
        try:
            return await handle_update
        finally:
            semaphore.release()

    async def _wait_for_handle_update_tasks(self, timeout: float | None) -> None:
        """
        Wait for updates that are still being handled in tasks started by polling

        Tasks still running after the timeout are cancelled, and their cancellation is awaited.

        :param timeout: Maximum time to wait in seconds (None = do not wait)
        """
        if timeout is None or not self._handle_update_tasks:
            return
        tasks = set(self._handle_update_tasks)
        loggers.dispatcher.info(
            "Waiting up to %s seconds for %d update(s) to be handled",
            timeout,
            len(tasks),
        )
        _, pending = await asyncio.wait(tasks, timeout=timeout)
        if not pending:
            return
        loggers.dispatcher.warning(
            "%d update(s) were not handled within %s seconds, cancelling them",
            len(pending),
            timeout,
        )
        for task in pending:
            task.cancel()
        await asyncio.wait(pending)

    async def _polling(
        self,
        bot: Bot,
        polling_timeout: int = 30,
        handle_as_tasks: bool = True,
        backoff_config: BackoffConfig = DEFAULT_BACKOFF_CONFIG,
        allowed_updates: list[str] | None = None,
        tasks_concurrency_limit: int | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Internal polling process

        :param bot:
        :param polling_timeout: Long-polling wait time
        :param handle_as_tasks: Run task for each event and no wait result
        :param backoff_config: backoff-retry config
        :param allowed_updates: List of the update types you want your bot to receive
        :param tasks_concurrency_limit: Maximum number of concurrent updates to process
            (None = no limit), used only if handle_as_tasks is True
        :param kwargs:
        :return:
        """
        user: User = await bot.me()
        loggers.dispatcher.info(
            "Run polling for bot @%s id=%d - %r",
            user.username,
            bot.id,
            user.full_name,
        )

        # Create semaphore if tasks_concurrency_limit is specified
        semaphore = None
        if tasks_concurrency_limit is not None and handle_as_tasks:
            semaphore = asyncio.Semaphore(tasks_concurrency_limit)

        try:
            async for update in self._listen_updates(
                bot,
                polling_timeout=polling_timeout,
                backoff_config=backoff_config,
                allowed_updates=allowed_updates,
            ):
                if handle_as_tasks and semaphore:
                    # Wait for capacity before creating the update coroutine.
                    await semaphore.acquire()
                handle_update = self._process_update(bot=bot, update=update, **kwargs)
                if handle_as_tasks:
                    if semaphore:
                        handle_update_task = asyncio.create_task(
                            self._process_with_semaphore(handle_update, semaphore),
                        )
                    else:
                        handle_update_task = asyncio.create_task(handle_update)

                    self._handle_update_tasks.add(handle_update_task)
                    handle_update_task.add_done_callback(self._handle_update_tasks.discard)
                else:
                    await handle_update
        finally:
            loggers.dispatcher.info(
                "Polling stopped for bot @%s id=%d - %r",
                user.username,
                bot.id,
                user.full_name,
            )

    async def _feed_webhook_update(self, bot: Bot, update: Update, **kwargs: Any) -> Any:
        """
        The same with `Dispatcher.process_update()` but returns real response instead of bool
        """
        log_token = _set_log_context(bot.id, update)  # the error record follows feed_update
        try:
            return await self.feed_update(bot, update, **kwargs)
        except Exception as e:
            loggers.event.exception(
                "Cause exception while process update id=%d by bot id=%d\n%s: %s",
                update.update_id,
                bot.id,
                e.__class__.__name__,
                e,
            )
            raise
        finally:
            loggers._current.reset(log_token)

    async def feed_webhook_update(
        self,
        bot: Bot,
        update: Update | dict[str, Any],
        _timeout: float = 55,
        **kwargs: Any,
    ) -> TelegramMethod[TelegramType] | None:
        ctx = contextvars.copy_context()
        loop = asyncio.get_running_loop()
        waiter = loop.create_future()

        def release_waiter(*_: Any) -> None:
            if not waiter.done():
                waiter.set_result(None)

        timeout_handle = loop.call_later(_timeout, release_waiter)

        # Raw updates are validated inside the timed task: the errors handlers of an invalid
        # update must not hold the answer past the deadline either
        process_updates: Future[Any] = asyncio.ensure_future(
            self._feed_webhook_update(bot=bot, update=update, **kwargs)
            if isinstance(update, Update)
            else self.feed_raw_update(bot=bot, update=update, **kwargs),
        )
        process_updates.add_done_callback(release_waiter, context=ctx)

        def process_response(task: Future[Any]) -> None:
            warnings.warn(
                "Detected slow response into webhook.\n"
                "Telegram is waiting for response only first 60 seconds and then re-send update.\n"
                "For preventing this situation response into webhook returned immediately "
                "and handler is moved to background and still processing update.",
                RuntimeWarning,
                stacklevel=2,
            )
            result = task.result()
            if isinstance(result, TelegramMethod):
                asyncio.ensure_future(self.silent_call_request(bot=bot, result=result))

        try:
            try:
                await waiter
            except CancelledError:  # pragma: no cover
                process_updates.remove_done_callback(release_waiter)
                process_updates.cancel()
                raise

            if process_updates.done():
                # TODO: handle exceptions
                response: Any = process_updates.result()
                if isinstance(response, TelegramMethod):
                    return response

            else:
                process_updates.remove_done_callback(release_waiter)
                process_updates.add_done_callback(process_response, context=ctx)

        finally:
            timeout_handle.cancel()

        return None

    async def stop_polling(self) -> None:
        """
        Execute this method if you want to stop polling programmatically

        :return:
        """
        if not self._running_lock.locked():
            msg = "Polling is not started"
            raise RuntimeError(msg)
        if not self._stop_signal or not self._stopped_signal:
            return
        # A handler that starts the stop is not waited for on shutdown, because it is
        # the one waiting for shutdown to complete. When the stop was already started
        # (by a signal or another call), the handler is waited for like any other one.
        handler_task = None
        if not self._stop_signal.is_set():
            current_task = asyncio.current_task()
            if current_task in self._handle_update_tasks:
                self._handle_update_tasks.discard(current_task)
                handler_task = current_task
        self._stop_signal.set()
        try:
            await self._stopped_signal.wait()
        finally:
            if handler_task is not None:
                # Keep a reference to the task until it is done, as polling does
                self._handle_update_tasks.add(handler_task)

    def _signal_stop_polling(self, sig: signal.Signals) -> None:
        if not self._running_lock.locked():
            return

        loggers.dispatcher.warning("Received %s signal", sig.name)
        if not self._stop_signal:
            return
        self._stop_signal.set()

    async def start_polling(
        self,
        *bots: Bot,
        polling_timeout: int = 10,
        handle_as_tasks: bool = True,
        backoff_config: BackoffConfig = DEFAULT_BACKOFF_CONFIG,
        allowed_updates: list[str] | UNSET_TYPE | None = UNSET,
        handle_signals: bool = True,
        close_bot_session: bool = True,
        tasks_concurrency_limit: int | None = None,
        tasks_shutdown_timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Polling runner

        :param bots: Bot instances (one or more)
        :param polling_timeout: Long-polling wait time
        :param handle_as_tasks: Run task for each event and no wait result
        :param backoff_config: backoff-retry config
        :param allowed_updates: List of the update types you want your bot to receive
               By default, all used update types are enabled (resolved from handlers)
        :param handle_signals: handle signals (SIGINT/SIGTERM)
        :param close_bot_session: close bot sessions on shutdown
        :param tasks_concurrency_limit: Maximum number of concurrent updates to process
            (None = no limit), used only if handle_as_tasks is True
        :param tasks_shutdown_timeout: Maximum time in seconds to wait on shutdown for updates
            that are still being handled, before shutdown callbacks run and bot sessions
            are closed; handlers still running after it are cancelled
            (None = do not wait), used only if handle_as_tasks is True
        :param kwargs: contextual data
        :return:
        """
        if not bots:
            msg = "At least one bot instance is required to start polling"
            raise ValueError(msg)
        if "bot" in kwargs:
            msg = (
                "Keyword argument 'bot' is not acceptable, "
                "the bot instance should be passed as positional argument"
            )
            raise ValueError(msg)

        async with self._running_lock:  # Prevent to run this method twice at a once
            if self._stop_signal is None:
                self._stop_signal = Event()
            if self._stopped_signal is None:
                self._stopped_signal = Event()

            if allowed_updates is UNSET:
                allowed_updates = self.resolve_used_update_types()

            self._stop_signal.clear()
            self._stopped_signal.clear()

            if handle_signals:
                loop = asyncio.get_running_loop()
                with suppress(NotImplementedError):  # pragma: no cover
                    # Signals handling is not supported on Windows
                    # It also can't be covered on Windows
                    loop.add_signal_handler(
                        signal.SIGTERM,
                        self._signal_stop_polling,
                        signal.SIGTERM,
                    )
                    loop.add_signal_handler(
                        signal.SIGINT,
                        self._signal_stop_polling,
                        signal.SIGINT,
                    )

            workflow_data = {
                "dispatcher": self,
                "bots": bots,
                **self.workflow_data,
                **kwargs,
            }
            if "bot" in workflow_data:
                workflow_data.pop("bot")

            await self.emit_startup(bot=bots[-1], **workflow_data)
            loggers.dispatcher.info("Start polling")
            try:
                tasks: list[asyncio.Task[Any]] = [
                    asyncio.create_task(
                        self._polling(
                            bot=bot,
                            handle_as_tasks=handle_as_tasks,
                            polling_timeout=polling_timeout,
                            backoff_config=backoff_config,
                            allowed_updates=allowed_updates,
                            tasks_concurrency_limit=tasks_concurrency_limit,
                            **workflow_data,
                        ),
                    )
                    for bot in bots
                ]
                tasks.append(asyncio.create_task(self._stop_signal.wait()))
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                for task in pending:
                    # (mostly) Graceful shutdown unfinished tasks
                    task.cancel()
                    with suppress(CancelledError):
                        await task
                # Let updates that are still being handled finish before shutdown
                await self._wait_for_handle_update_tasks(timeout=tasks_shutdown_timeout)
                # Wait finished tasks to propagate unhandled exceptions
                await asyncio.gather(*done)

            finally:
                loggers.dispatcher.info("Polling stopped")
                try:
                    await self.emit_shutdown(bot=bots[-1], **workflow_data)
                finally:
                    if close_bot_session:
                        await asyncio.gather(*(bot.session.close() for bot in bots))
                self._stopped_signal.set()

    def run_polling(
        self,
        *bots: Bot,
        polling_timeout: int = 10,
        handle_as_tasks: bool = True,
        backoff_config: BackoffConfig = DEFAULT_BACKOFF_CONFIG,
        allowed_updates: list[str] | UNSET_TYPE | None = UNSET,
        handle_signals: bool = True,
        close_bot_session: bool = True,
        tasks_concurrency_limit: int | None = None,
        tasks_shutdown_timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Run many bots with polling

        :param bots: Bot instances (one or more)
        :param polling_timeout: Long-polling wait time
        :param handle_as_tasks: Run task for each event and no wait result
        :param backoff_config: backoff-retry config
        :param allowed_updates: List of the update types you want your bot to receive
        :param handle_signals: handle signals (SIGINT/SIGTERM)
        :param close_bot_session: close bot sessions on shutdown
        :param tasks_concurrency_limit: Maximum number of concurrent updates to process
            (None = no limit), used only if handle_as_tasks is True
        :param tasks_shutdown_timeout: Maximum time in seconds to wait on shutdown for updates
            that are still being handled, before shutdown callbacks run and bot sessions
            are closed; handlers still running after it are cancelled
            (None = do not wait), used only if handle_as_tasks is True
        :param kwargs: contextual data
        :return:
        """
        with suppress(KeyboardInterrupt):
            coro = self.start_polling(
                *bots,
                **kwargs,
                polling_timeout=polling_timeout,
                handle_as_tasks=handle_as_tasks,
                backoff_config=backoff_config,
                allowed_updates=allowed_updates,
                handle_signals=handle_signals,
                close_bot_session=close_bot_session,
                tasks_concurrency_limit=tasks_concurrency_limit,
                tasks_shutdown_timeout=tasks_shutdown_timeout,
            )

            try:
                import uvloop

            except ImportError:
                return asyncio.run(coro)

            else:
                with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
                    return runner.run(coro)
