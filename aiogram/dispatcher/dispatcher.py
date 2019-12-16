import asyncio
from asyncio import Lock
from typing import Any, AsyncGenerator, Dict, Optional

from .. import loggers
from ..api.client.bot import Bot
from ..api.methods import TelegramMethod
from ..api.types import Update, User
from ..utils.exceptions import TelegramAPIError
from .router import Router


class Dispatcher(Router):
    """
    Root router
    """

    def __init__(self, **kwargs: Any) -> None:
        super(Dispatcher, self).__init__(**kwargs)
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

    async def feed_update(
        self, bot: Bot, update: Update, **kwargs: Any
    ) -> AsyncGenerator[Any, None]:
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
            async for result in self.update_handler.trigger(update, bot=bot, **kwargs):
                yield result
                handled = True
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

    async def feed_raw_update(
        self, bot: Bot, update: Dict[str, Any], **kwargs: Any
    ) -> AsyncGenerator[Any, None]:
        """
        Main entry point for incoming updates with automatic Dict->Update serializer

        :param bot:
        :param update:
        :param kwargs:
        """
        parsed_update = Update(**update)
        async for result in self.feed_update(bot=bot, update=parsed_update, **kwargs):
            yield result

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
    async def _silent_call_request(cls, result: TelegramMethod) -> None:
        """
        Simulate answer into WebHook

        :param result:
        :return:
        """
        try:
            await result
        except TelegramAPIError as e:
            # In due to WebHook mechanism doesn't allows to get response for
            # requests called in answer to WebHook request.
            # Need to skip unsuccessful responses.
            # For debugging here is added logging.
            loggers.dispatcher.error("Failed to make answer: %s: %s", e.__class__.__name__, e)

    async def process_update(
        self, update: Update, bot: Bot, call_answer: bool = True, **kwargs: Any
    ) -> bool:
        """
        Propagate update to event listeners

        :param update: instance of Update
        :param bot: instance of Bot
        :param call_answer: need to execute response as Telegram method (like answer into webhook)
        :param kwargs: contextual data for middlewares, filters and handlers
        :return: status
        """
        try:
            async for result in self.feed_update(bot, update, **kwargs):
                if call_answer and isinstance(result, TelegramMethod):
                    await self._silent_call_request(result)
                return True

        except Exception as e:
            loggers.dispatcher.exception(
                "Cause exception while process update id=%d by bot id=%d\n%s: %s",
                update.update_id,
                bot.id,
                e.__class__.__name__,
                e,
            )
            return True  # because update was processed but unsuccessful

        return False

    async def _polling(self, bot: Bot, **kwargs: Any) -> None:
        """
        Internal polling process

        :param bot:
        :param kwargs:
        :return:
        """
        async for update in self._listen_updates(bot):
            await self.process_update(update=update, bot=bot, **kwargs)

    async def _run_polling(self, *bots: Bot, **kwargs: Any) -> None:
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
            return asyncio.run(self._run_polling(*bots, **kwargs))
        except (KeyboardInterrupt, SystemExit):  # pragma: no cover
            # Allow to graceful shutdown
            pass
