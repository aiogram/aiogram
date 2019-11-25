from typing import AsyncGenerator, Optional

from ..api.client.bot import Bot
from ..api.methods import TelegramMethod
from ..api.types import Update
from .router import Router


class Dispatcher(Router):
    @property
    def parent_router(self) -> Optional[Router]:
        return None

    @parent_router.setter
    def parent_router(self, value) -> Optional[Router]:
        # Dispatcher is root Router then configuring parent router is not allowed
        raise RuntimeError("Dispatcher can not be attached to another Router.")

    async def feed_update(self, bot: Bot, update: Update, **kwargs):
        """
        Main entry point for incoming updates

        :param bot:
        :param update:
        :return:
        """
        Bot.set_current(bot)
        async for result in self.update_handler.trigger(update, bot=bot, **kwargs):
            yield result

    @classmethod
    async def listen_updates(cls, bot: Bot) -> AsyncGenerator[Update, None]:
        update_id: Optional[int] = None
        while True:
            for update in await bot.get_updates(offset=update_id):
                yield update
                update_id = update.update_id + 1

    async def polling(self, bot: Bot):
        self.emit_startup(bot=bot)
        try:
            async for update in self.listen_updates(bot):
                async for result in self.feed_update(bot, update):
                    if isinstance(result, TelegramMethod):
                        await result
        finally:
            self.emit_shutdown(bot=bot)
