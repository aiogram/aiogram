import asyncio
import logging

from .filters import CommandsFilter, RegexpFilter, ContentTypeFilter
from .handler import Handler
from ..bot import AIOGramBot
from ..types.message import ContentType

log = logging.getLogger(__name__)


class Dispatcher:
    def __init__(self, bot, loop=None):
        self.bot: AIOGramBot = bot
        if loop is None:
            loop = self.bot.loop

        self.loop = loop

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
            self.loop.create_task(self.updates.notify(update))

    async def process_update(self, update):
        if update.message:
            await self.messages.notify(update.message)

    async def start_pooling(self, timeout=20, relax=0.1):
        if self._pooling:
            raise RuntimeError('Pooling already started')
        log.info('Start pooling.')

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
                log.info(f"Received {len(updates)} updates.")
                offset = updates[-1].update_id + 1
                await self.process_updates(updates)

            await asyncio.sleep(relax)

        log.warning('Pooling is stopped.')

    def stop_pooling(self):
        self._pooling = False

    def message_handler(self, commands=None, regexp=None, content_type=None, func=None,
                        custom_filters=None):
        if commands is None:
            commands = []
        if content_type is None:
            content_type = [ContentType.TEXT]
        if custom_filters is None:
            custom_filters = []

        filters_preset = []
        if commands:
            if isinstance(commands, str):
                commands = [commands]
            filters_preset.append(CommandsFilter(commands))

        if regexp:
            filters_preset.append(RegexpFilter(regexp))

        if content_type:
            filters_preset.append(ContentTypeFilter(content_type))

        if func:
            filters_preset.append(func)

        if custom_filters:
            filters_preset += custom_filters

        def decorator(func):
            self.messages.register(func, filters_preset)
            return func

        return decorator

    def __del__(self):
        self._pooling = False
