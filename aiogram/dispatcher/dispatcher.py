from __future__ import annotations

import asyncio
import contextvars
import warnings
from asyncio import CancelledError, Future, Lock
from typing import Any, AsyncGenerator, Dict, Optional, Union

from .. import loggers
from ..api.client.bot import Bot
from ..api.methods import TelegramMethod
from ..api.types import Update, User
from ..utils.exceptions import TelegramAPIError
from .event.bases import NOT_HANDLED
from .middlewares.update_processing_context import UserContextMiddleware
from .router import Router


class Dispatcher(Router):
    """
    Root router
    """

    def __init__(self, **kwargs: Any) -> None:
        super(Dispatcher, self).__init__(**kwargs)
        self._running_lock = Lock()

        # Default middleware is needed for contextual features
        self.update.outer_middleware(UserContextMiddleware())

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
            handled = response is not NOT_HANDLED
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
        handled = False
        try:
            response = await self.feed_update(bot, update, **kwargs)
            handled = handled is not NOT_HANDLED
            if call_answer and isinstance(response, TelegramMethod):
                await self._silent_call_request(bot=bot, result=response)
            return handled

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
        self, bot: Bot, update: Union[Update, Dict[str, Any]], _timeout: int = 55, **kwargs: Any
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
                    request = response.build_request()
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
                    await bot.close()
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
