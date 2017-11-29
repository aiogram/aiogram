import asyncio
import time

from aiogram.dispatcher import BaseStorage, Dispatcher, ctx

DEFAULT_RATE_LIMIT = .1

KEY = 'key'
LAST_CALL = 'called_at'
RATE_LIMIT = 'rate_limit'
RESULT = 'result'
EXCEEDED_COUNT = 'exceeded'
DELTA = 'delta'
THROTTLE_MANAGER = '$throttle_manager'


class ThrottleError(Exception):
    def __init__(self, **kwargs):
        self.key = kwargs.pop(KEY, '<None>')
        self.called_at = kwargs.pop(LAST_CALL, time.time())
        self.rate = kwargs.pop(RATE_LIMIT, None)
        self.result = kwargs.pop(RESULT, False)
        self.exceeded_count = kwargs.pop(EXCEEDED_COUNT, 0)
        self.delta = kwargs.pop(DELTA, 0)
        self.user = kwargs.pop('user', None)
        self.chat = kwargs.pop('chat', None)

    def __str__(self):
        return f"Rate limit exceeded! (Limit: {self.rate} s, " \
               f"exceeded: {self.exceeded_count}, " \
               f"time delta: {round(self.delta, 3)} s)"


class Bucket:
    """
    Throttling manager
    """

    def __init__(self, dispatcher, rate_limit=DEFAULT_RATE_LIMIT, storage: BaseStorage = None, no_error=False):
        """
        Initialize throttle manager

        :param dispatcher: instance of Dispatcher
        :param rate_limit: limit in seconds
        :param storage:
        :param no_error: return boolean value instead of raising error
        """
        if storage is None:
            storage = dispatcher.storage
        if not storage.has_bucket():
            raise TypeError('This storage does not provide Bucket!')

        self._dispatcher: Dispatcher = dispatcher
        self._loop: asyncio.BaseEventLoop = self._dispatcher.loop
        self._rate_limit = rate_limit
        self._storage = storage
        self._no_error = no_error

        dispatcher.bot[THROTTLE_MANAGER] = self

    async def throttle(self, key, *, rate=None, user=None, chat=None, no_error=None) -> bool:
        """
        Execute throttling manager.
        Return True limit is not exceeded otherwise raise ThrottleError or return False

        :param key: key in storage
        :param rate: limit (by default is equals with default rate limit)
        :param user: user id
        :param chat: chat id
        :param no_error: return boolean value instead of raising error
        :return: bool
        """
        if no_error is None:
            no_error = self._no_error
        if rate is None:
            rate = self._rate_limit
        if user is None and chat is None:
            user = ctx.get_user()
            chat = ctx.get_chat()

        # Detect current time
        now = time.time()

        bucket = await self._storage.get_bucket(chat=chat, user=user)

        # Fix bucket
        if bucket is None:
            bucket = {key: {}}
        if key not in bucket:
            bucket[key] = {}
        data = bucket[key]

        # Calculate
        called = data.get(LAST_CALL, now)
        delta = now - called
        result = delta >= rate or delta <= 0

        # Save results
        data[RESULT] = result
        data[RATE_LIMIT] = rate
        data[LAST_CALL] = now
        data[DELTA] = delta
        if not result:
            data[EXCEEDED_COUNT] += 1
        else:
            data[EXCEEDED_COUNT] = 1
        bucket[key].update(data)
        await self._storage.set_bucket(chat=chat, user=user, bucket=bucket)

        if not result and not no_error:
            # Raise if that is allowed
            raise ThrottleError(key=key, chat=chat, user=user, **data)
        return result

    async def release_key(self, key, chat=None, user=None):
        """
        Release blocked key

        :param key:
        :param chat:
        :param user:
        :return:
        """
        if user is None and chat is None:
            user = ctx.get_user()
            chat = ctx.get_chat()
        bucket = await self._storage.get_bucket(chat=chat, user=user)
        if bucket and key in bucket:
            del bucket['key']
            await self._storage.set_bucket(chat=chat, user=user, bucket=bucket)
            return True
        return False


async def throttle(key, rate=None, no_error=None):
    """
    Alias for Bucket.throttle(...)

    :param key:
    :param rate:
    :param no_error:
    :return:
    """
    bot = ctx.get_bot()
    bucket = bot.get(THROTTLE_MANAGER)
    if not bucket:
        raise RuntimeError('Can\'t be found Bucket!')
    return await bucket.throttle(key=key, rate=rate, no_error=no_error)
