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
    def __init__(self, **kwargs):
        super(Dispatcher, self).__init__(**kwargs)
        self._running_lock = Lock()

    @property
    def parent_router(self) -> Optional[Router]:
        return None

    @parent_router.setter
    def parent_router(self, value) -> Optional[Router]:
        # Dispatcher is root Router then configuring parent router is not allowed
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
        async for result in self.update_handler.trigger(update, bot=bot, **kwargs):
            yield result
            handled = True

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
            return True

        return False

    async def _polling(self, bot: Bot, **kwargs: Any) -> None:
        async for update in self._listen_updates(bot):
            await self.process_update(update=update, bot=bot, **kwargs)

    async def _run_polling(self, *bots: Bot, **kwargs: Any) -> None:
        async with self._running_lock:  # Prevent to run_polling this method twice at a once
            workflow_data = {"dispatcher": self, "bots": bots, "bot": bots[-1]}
            workflow_data.update(kwargs)
            await self.emit_startup(**workflow_data)
            loggers.dispatcher.info("Start poling")
            try:
                coro_list = []
                for bot in bots:
                    async with bot.context(auto_close=False):
                        user: User = await bot.me()
                        loggers.dispatcher.info(
                            "Run polling for bot @%s id=%d - %r",
                            user.username,
                            bot.id,
                            user.full_name,
                        )
                        coro_list.append(self._polling(bot=bot, **kwargs))
                await asyncio.gather(*coro_list)
            finally:
                for bot in bots:
                    await bot.close()
                loggers.dispatcher.info("Polling stopped")
                await self.emit_shutdown(**workflow_data)

    def run_polling(self, *bots: Bot, **kwargs: Any):
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
