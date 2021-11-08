from __future__ import annotations

import asyncio
import contextvars
import warnings
from asyncio import CancelledError, Future, Lock
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from .. import loggers
from ..client.bot import Bot
from ..exceptions import TelegramAPIError, TelegramNetworkError, TelegramServerError
from ..methods import GetUpdates, TelegramMethod
from ..types import Update, User
from ..types.update import UpdateTypeLookupError
from ..utils.backoff import Backoff, BackoffConfig
from .event.bases import UNHANDLED, SkipHandler
from .event.telegram import TelegramEventObserver
from .fsm.middleware import FSMContextMiddleware
from .fsm.storage.base import BaseStorage
from .fsm.storage.memory import MemoryStorage
from .fsm.strategy import FSMStrategy
from .middlewares.error import ErrorsMiddleware
from .middlewares.user_context import UserContextMiddleware
from .router import Router

DEFAULT_BACKOFF_CONFIG = BackoffConfig(min_delay=1.0, max_delay=5.0, factor=1.3, jitter=0.1)


class Dispatcher(Router):
    """
    Root router
    """

    def __init__(
        self,
        storage: Optional[BaseStorage] = None,
        fsm_strategy: FSMStrategy = FSMStrategy.USER_IN_CHAT,
        isolate_events: bool = False,
        **kwargs: Any,
    ) -> None:
        super(Dispatcher, self).__init__(**kwargs)

        # Telegram API provides originally only one event type - Update
        # For making easily interactions with events here is registered handler which helps
        # to separate Update to different event types like Message, CallbackQuery and etc.
        self.update = self.observers["update"] = TelegramEventObserver(
            router=self, event_name="update"
        )
        self.update.register(self._listen_update)

        # Error handlers should works is out of all other functions and be registered before all other middlewares
        self.update.outer_middleware(ErrorsMiddleware(self))
        # User context middleware makes small optimization for all other builtin
        # middlewares via caching the user and chat instances in the event context
        self.update.outer_middleware(UserContextMiddleware())
        # FSM middleware should always be registered after User context middleware
        # because here is used context from previous step
        self.fsm = FSMContextMiddleware(
            storage=storage if storage else MemoryStorage(),
            strategy=fsm_strategy,
            isolate_events=isolate_events,
        )
        self.update.outer_middleware(self.fsm)

        self._running_lock = Lock()

    @property
    def parent_router(self) -> None:
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
        raise RuntimeError("Dispatcher can not be attached to another Router.")

    async def feed_update(self, bot: Bot, update: Update, **kwargs: Any) -> Any:
        """
        Main entry point for incoming updates
        Response of this method can be used as Webhook response

        :param bot:
        :param update:
        """
        loop = asyncio.get_running_loop()
        handled = False
        start_time = loop.time()

        token = Bot.set_current(bot)
        try:
            kwargs.update(bot=bot)
            response = await self.update.wrap_outer_middleware(self.update.trigger, update, kwargs)
            handled = response is not UNHANDLED
            return response
        finally:
            finish_time = loop.time()
            duration = (finish_time - start_time) * 1000
            loggers.dispatcher.info(
                "Update id=%s is %s. Duration %d ms by bot id=%d",
                update.update_id,
                "handled" if handled else "not handled",
                duration,
                bot.id,
            )
            Bot.reset_current(token)

    async def feed_raw_update(self, bot: Bot, update: Dict[str, Any], **kwargs: Any) -> Any:
        """
        Main entry point for incoming updates with automatic Dict->Update serializer

        :param bot:
        :param update:
        :param kwargs:
        """
        parsed_update = Update(**update)
        return await self.feed_update(bot=bot, update=parsed_update, **kwargs)

    @classmethod
    async def _listen_updates(
        cls,
        bot: Bot,
        polling_timeout: int = 30,
        backoff_config: BackoffConfig = DEFAULT_BACKOFF_CONFIG,
        allowed_updates: Optional[List[str]] = None,
    ) -> AsyncGenerator[Update, None]:
        """
        Endless updates reader with correctly handling any server-side or connection errors.

        So you may not worry that the polling will stop working.
        """
        backoff = Backoff(config=backoff_config)
        get_updates = GetUpdates(timeout=polling_timeout, allowed_updates=allowed_updates)
        kwargs = {}
        if bot.session.timeout:
            # Request timeout can be lower than session timeout ant that's OK.
            # To prevent false-positive TimeoutError we should wait longer than polling timeout
            kwargs["request_timeout"] = int(bot.session.timeout + polling_timeout)
        while True:
            try:
                updates = await bot(get_updates, **kwargs)
            except (TelegramNetworkError, TelegramServerError) as e:
                # In cases when Telegram Bot API was inaccessible don't need to stop polling process
                # because some of developers can't make auto-restarting of the script
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
            backoff.reset()

            for update in updates:
                yield update
                # The getUpdates method returns the earliest 100 unconfirmed updates.
                # To confirm an update, use the offset parameter when calling getUpdates
                # All updates with update_id less than or equal to offset will be marked as confirmed on the server
                # and will no longer be returned.
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
        try:
            update_type = update.event_type
            event = update.event
        except UpdateTypeLookupError:
            warnings.warn(
                "Detected unknown update type.\n"
                "Seems like Telegram Bot API was updated and you have "
                "installed not latest version of aiogram framework",
                RuntimeWarning,
            )
            raise SkipHandler()

        kwargs.update(event_update=update)

        return await self.propagate_event(update_type=update_type, event=event, **kwargs)

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
            # In due to WebHook mechanism doesn't allows to get response for
            # requests called in answer to WebHook request.
            # Need to skip unsuccessful responses.
            # For debugging here is added logging.
            loggers.dispatcher.error("Failed to make answer: %s: %s", e.__class__.__name__, e)

    async def _process_update(
        self, bot: Bot, update: Update, call_answer: bool = True, **kwargs: Any
    ) -> bool:
        """
        Propagate update to event listeners

        :param bot: instance of Bot
        :param update: instance of Update
        :param call_answer: need to execute response as Telegram method (like answer into webhook)
        :param kwargs: contextual data for middlewares, filters and handlers
        :return: status
        """
        try:
            response = await self.feed_update(bot, update, **kwargs)
            if call_answer and isinstance(response, TelegramMethod):
                await self.silent_call_request(bot=bot, result=response)
            return response is not UNHANDLED

        except Exception as e:
            loggers.dispatcher.exception(
                "Cause exception while process update id=%d by bot id=%d\n%s: %s",
                update.update_id,
                bot.id,
                e.__class__.__name__,
                e,
            )
            return True  # because update was processed but unsuccessful

    async def _polling(
        self,
        bot: Bot,
        polling_timeout: int = 30,
        handle_as_tasks: bool = True,
        backoff_config: BackoffConfig = DEFAULT_BACKOFF_CONFIG,
        allowed_updates: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Internal polling process

        :param bot:
        :param kwargs:
        :return:
        """
        async for update in self._listen_updates(
            bot,
            polling_timeout=polling_timeout,
            backoff_config=backoff_config,
            allowed_updates=allowed_updates,
        ):
            handle_update = self._process_update(bot=bot, update=update, **kwargs)
            if handle_as_tasks:
                asyncio.create_task(handle_update)
            else:
                await handle_update

    async def _feed_webhook_update(self, bot: Bot, update: Update, **kwargs: Any) -> Any:
        """
        The same with `Dispatcher.process_update()` but returns real response instead of bool
        """
        try:
            return await self.feed_update(bot, update, **kwargs)
        except Exception as e:
            loggers.dispatcher.exception(
                "Cause exception while process update id=%d by bot id=%d\n%s: %s",
                update.update_id,
                bot.id,
                e.__class__.__name__,
                e,
            )
            raise

    async def feed_webhook_update(
        self, bot: Bot, update: Union[Update, Dict[str, Any]], _timeout: float = 55, **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(update, Update):  # Allow to use raw updates
            update = Update(**update)

        ctx = contextvars.copy_context()
        loop = asyncio.get_running_loop()
        waiter = loop.create_future()

        def release_waiter(*args: Any) -> None:
            if not waiter.done():
                waiter.set_result(None)

        timeout_handle = loop.call_later(_timeout, release_waiter)

        process_updates: Future[Any] = asyncio.ensure_future(
            self._feed_webhook_update(bot=bot, update=update, **kwargs)
        )
        process_updates.add_done_callback(release_waiter, context=ctx)

        def process_response(task: Future[Any]) -> None:
            warnings.warn(
                "Detected slow response into webhook.\n"
                "Telegram is waiting for response only first 60 seconds and then re-send update.\n"
                "For preventing this situation response into webhook returned immediately "
                "and handler is moved to background and still processing update.",
                RuntimeWarning,
            )
            try:
                result = task.result()
            except Exception as e:
                raise e
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
                    request = response.build_request(bot=bot)
                    return request.render_webhook_request()

            else:
                process_updates.remove_done_callback(release_waiter)
                process_updates.add_done_callback(process_response, context=ctx)

        finally:
            timeout_handle.cancel()

        return None

    async def start_polling(
        self,
        *bots: Bot,
        polling_timeout: int = 10,
        handle_as_tasks: bool = True,
        backoff_config: BackoffConfig = DEFAULT_BACKOFF_CONFIG,
        allowed_updates: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Polling runner

        :param bots:
        :param polling_timeout:
        :param handle_as_tasks:
        :param kwargs:
        :param backoff_config:
        :param allowed_updates:
        :return:
        """
        async with self._running_lock:  # Prevent to run this method twice at a once
            workflow_data = {"dispatcher": self, "bots": bots, "bot": bots[-1]}
            workflow_data.update(kwargs)
            await self.emit_startup(**workflow_data)
            loggers.dispatcher.info("Start poling")
            try:
                coro_list = []
                for bot in bots:
                    user: User = await bot.me()
                    loggers.dispatcher.info(
                        "Run polling for bot @%s id=%d - %r", user.username, bot.id, user.full_name
                    )
                    coro_list.append(
                        self._polling(
                            bot=bot,
                            handle_as_tasks=handle_as_tasks,
                            polling_timeout=polling_timeout,
                            backoff_config=backoff_config,
                            allowed_updates=allowed_updates,
                            **kwargs,
                        )
                    )
                await asyncio.gather(*coro_list)
            finally:
                loggers.dispatcher.info("Polling stopped")
                try:
                    await self.emit_shutdown(**workflow_data)
                finally:
                    for bot in bots:  # Close sessions
                        await bot.session.close()

    def run_polling(
        self,
        *bots: Bot,
        polling_timeout: int = 30,
        handle_as_tasks: bool = True,
        backoff_config: BackoffConfig = DEFAULT_BACKOFF_CONFIG,
        allowed_updates: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Run many bots with polling

        :param bots: Bot instances
        :param polling_timeout: Poling timeout
        :param backoff_config:
        :param handle_as_tasks: Run task for each event and no wait result
        :param allowed_updates: List of the update types you want your bot to receive
        :param kwargs: contextual data
        :return:
        """
        try:
            return asyncio.run(
                self.start_polling(
                    *bots,
                    **kwargs,
                    polling_timeout=polling_timeout,
                    handle_as_tasks=handle_as_tasks,
                    backoff_config=backoff_config,
                    allowed_updates=allowed_updates,
                )
            )
        except (KeyboardInterrupt, SystemExit):  # pragma: no cover
            # Allow to graceful shutdown
            pass
