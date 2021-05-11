from __future__ import annotations

import asyncio
import contextvars
import warnings
from asyncio import CancelledError, Future, Lock
from typing import Any, AsyncGenerator, Dict, Optional, Union

from .. import loggers
from ..client.bot import Bot
from ..methods import TelegramMethod
from ..types import TelegramObject, Update, User
from ..utils.exceptions import TelegramAPIError
from .event.bases import UNHANDLED, SkipHandler
from .event.telegram import TelegramEventObserver
from .fsm.context import FSMContext
from .fsm.middleware import FSMContextMiddleware
from .fsm.storage.base import BaseStorage
from .fsm.storage.memory import MemoryStorage
from .fsm.strategy import FSMStrategy
from .middlewares.error import ErrorsMiddleware
from .middlewares.user_context import UserContextMiddleware
from .router import Router


class Dispatcher(Router):
    """
    Root router
    """

    def __init__(
        self,
        storage: Optional[BaseStorage] = None,
        fsm_strategy: FSMStrategy = FSMStrategy.USER_IN_CHAT,
        isolate_events: bool = True,
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
        Dispatcher has no parent router

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

        :param bot:
        :param update:
        """
        loop = asyncio.get_running_loop()
        handled = False
        start_time = loop.time()

        Bot.set_current(bot)
        try:
            response = await self.update.trigger(update, bot=bot, **kwargs)
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
    async def _listen_updates(cls, bot: Bot) -> AsyncGenerator[Update, None]:
        """
        Infinity updates reader
        """
        update_id: Optional[int] = None
        while True:
            # TODO: Skip restarting telegram error
            for update in await bot.get_updates(offset=update_id):
                yield update
                update_id = update.update_id + 1

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
        event: TelegramObject
        if update.message:
            update_type = "message"
            event = update.message
        elif update.edited_message:
            update_type = "edited_message"
            event = update.edited_message
        elif update.channel_post:
            update_type = "channel_post"
            event = update.channel_post
        elif update.edited_channel_post:
            update_type = "edited_channel_post"
            event = update.edited_channel_post
        elif update.inline_query:
            update_type = "inline_query"
            event = update.inline_query
        elif update.chosen_inline_result:
            update_type = "chosen_inline_result"
            event = update.chosen_inline_result
        elif update.callback_query:
            update_type = "callback_query"
            event = update.callback_query
        elif update.shipping_query:
            update_type = "shipping_query"
            event = update.shipping_query
        elif update.pre_checkout_query:
            update_type = "pre_checkout_query"
            event = update.pre_checkout_query
        elif update.poll:
            update_type = "poll"
            event = update.poll
        elif update.poll_answer:
            update_type = "poll_answer"
            event = update.poll_answer
        elif update.my_chat_member:
            update_type = "my_chat_member"
            event = update.my_chat_member
        elif update.chat_member:
            update_type = "chat_member"
            event = update.chat_member
        else:
            warnings.warn(
                "Detected unknown update type.\n"
                "Seems like Telegram Bot API was updated and you have "
                "installed not latest version of aiogram framework",
                RuntimeWarning,
            )
            raise SkipHandler

        kwargs.update(event_update=update)

        for router in self.chain:
            kwargs.update(event_router=router)
            observer = router.observers[update_type]
            response = await observer.trigger(event, update=update, **kwargs)
            if response is not UNHANDLED:
                break
        else:
            response = UNHANDLED

        return response

    @classmethod
    async def _silent_call_request(cls, bot: Bot, result: TelegramMethod[Any]) -> None:
        """
        Simulate answer into WebHook

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
                await self._silent_call_request(bot=bot, result=response)
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

    async def _polling(self, bot: Bot, **kwargs: Any) -> None:
        """
        Internal polling process

        :param bot:
        :param kwargs:
        :return:
        """
        async for update in self._listen_updates(bot):
            await self._process_update(bot=bot, update=update, **kwargs)

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
                asyncio.ensure_future(self._silent_call_request(bot=bot, result=result))

        try:
            try:
                await waiter
            except CancelledError:  # pragma: nocover
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

    async def start_polling(self, *bots: Bot, **kwargs: Any) -> None:
        """
        Polling runner

        :param bots:
        :param kwargs:
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
                    coro_list.append(self._polling(bot=bot, **kwargs))
                await asyncio.gather(*coro_list)
            finally:
                for bot in bots:  # Close sessions
                    await bot.session.close()
                loggers.dispatcher.info("Polling stopped")
                await self.emit_shutdown(**workflow_data)

    def run_polling(self, *bots: Bot, **kwargs: Any) -> None:
        """
        Run many bots with polling

        :param bots:
        :param kwargs:
        :return:
        """
        try:
            return asyncio.run(self.start_polling(*bots, **kwargs))
        except (KeyboardInterrupt, SystemExit):  # pragma: no cover
            # Allow to graceful shutdown
            pass

    def current_state(self, user_id: int, chat_id: int) -> FSMContext:
        return self.fsm.get_context(user_id=user_id, chat_id=chat_id)
