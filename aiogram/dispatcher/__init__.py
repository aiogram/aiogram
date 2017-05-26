import asyncio
import logging

from .handler import Handler
from ..bot import AIOGramBot

log = logging.getLogger(__name__)


class Dispatcher:
    def __init__(self, bot):
        self.bot: AIOGramBot = bot

        self.last_update_id = 0
        self.updates = Handler(self)
        self.messages = Handler(self)
        self.commands = Handler(self)

        self.updates.register(self.process_update)

        self._pooling = False

    async def skip_updates(self):
        total = 0
        updates = await self.bot.get_updates(offset=self.last_update_id, timeout=1)
        while updates:
            total += len(updates)
            for update in updates:
                if update.update_id > self.last_update_id:
                    self.last_update_id = update.update_id
            updates = await self.bot.get_updates(offset=self.last_update_id + 1, timeout=1)
        return total

    async def process_updates(self, updates):
        for update in updates:
            self.bot.loop.create_task(self.updates.notify(update))

    async def process_update(self, update):
        if update.message:
            await self.messages.notify(update.message)

    async def start_pooling(self, timeout=20, relax=0.1):
        if self._pooling:
            raise RuntimeError('Pooling already started')
        self._pooling = True
        offset = None
        while self._pooling:
            try:
                updates = await self.bot.get_updates(offset=offset, timeout=timeout)
            except Exception as e:
                log.exception('Cause exception while getting updates')
                await asyncio.sleep(relax)
                continue

            if updates:
                offset = updates[-1].update_id + 1
                await self.process_updates(updates)

            await asyncio.sleep(relax)

    def stop_pooling(self):
        self._pooling = False
