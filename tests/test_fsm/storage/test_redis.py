import pytest

from aiogram.fsm.storage.base import DEFAULT_DESTINY, StorageKey
from aiogram.fsm.storage.redis import (
    DefaultKeyBuilder,
    RedisEventIsolation,
    RedisStorage,
)

PREFIX = "test"
BOT_ID = 42
CHAT_ID = -1
USER_ID = 2
THREAD_ID = 3
BUSINESS_CONNECTION_ID = "4"
FIELD = "data"


class TestRedisDefaultKeyBuilder:
    @pytest.mark.parametrize(
        "key_builder,result",
        [
            [
                DefaultKeyBuilder(
                    prefix=PREFIX,
                    with_bot_id=True,
                    with_destiny=True,
                    with_business_connection_id=True,
                ),
                f"{PREFIX}:{BOT_ID}:{BUSINESS_CONNECTION_ID}:{CHAT_ID}:{USER_ID}:{DEFAULT_DESTINY}:{FIELD}",
            ],
            [
                DefaultKeyBuilder(prefix=PREFIX, with_bot_id=True, with_destiny=True),
                f"{PREFIX}:{BOT_ID}:{CHAT_ID}:{USER_ID}:{DEFAULT_DESTINY}:{FIELD}",
            ],
            [
                DefaultKeyBuilder(
                    prefix=PREFIX, with_bot_id=True, with_business_connection_id=True
                ),
                f"{PREFIX}:{BOT_ID}:{BUSINESS_CONNECTION_ID}:{CHAT_ID}:{USER_ID}:{FIELD}",
            ],
            [
                DefaultKeyBuilder(prefix=PREFIX, with_bot_id=True),
                f"{PREFIX}:{BOT_ID}:{CHAT_ID}:{USER_ID}:{FIELD}",
            ],
            [
                DefaultKeyBuilder(
                    prefix=PREFIX, with_destiny=True, with_business_connection_id=True
                ),
                f"{PREFIX}:{BUSINESS_CONNECTION_ID}:{CHAT_ID}:{USER_ID}:{DEFAULT_DESTINY}:{FIELD}",
            ],
            [
                DefaultKeyBuilder(prefix=PREFIX, with_destiny=True),
                f"{PREFIX}:{CHAT_ID}:{USER_ID}:{DEFAULT_DESTINY}:{FIELD}",
            ],
            [
                DefaultKeyBuilder(prefix=PREFIX, with_business_connection_id=True),
                f"{PREFIX}:{BUSINESS_CONNECTION_ID}:{CHAT_ID}:{USER_ID}:{FIELD}",
            ],
            [DefaultKeyBuilder(prefix=PREFIX), f"{PREFIX}:{CHAT_ID}:{USER_ID}:{FIELD}"],
        ],
    )
    async def test_generate_key(self, key_builder: DefaultKeyBuilder, result: str):
        key = StorageKey(
            chat_id=CHAT_ID,
            user_id=USER_ID,
            bot_id=BOT_ID,
            business_connection_id=BUSINESS_CONNECTION_ID,
            destiny=DEFAULT_DESTINY,
        )
        assert key_builder.build(key, FIELD) == result

    async def test_destiny_check(self):
        key_builder = DefaultKeyBuilder(
            with_destiny=False,
        )
        key = StorageKey(chat_id=CHAT_ID, user_id=USER_ID, bot_id=BOT_ID)
        assert key_builder.build(key, FIELD)

        key = StorageKey(
            chat_id=CHAT_ID, user_id=USER_ID, bot_id=BOT_ID, destiny="CUSTOM_TEST_DESTINY"
        )
        with pytest.raises(ValueError):
            key_builder.build(key, FIELD)

    def test_thread_id(self):
        key_builder = DefaultKeyBuilder(
            prefix=PREFIX,
        )
        key = StorageKey(
            chat_id=CHAT_ID,
            user_id=USER_ID,
            bot_id=BOT_ID,
            thread_id=THREAD_ID,
            destiny=DEFAULT_DESTINY,
        )
        assert key_builder.build(key, FIELD) == f"{PREFIX}:{CHAT_ID}:{THREAD_ID}:{USER_ID}:{FIELD}"

    def test_create_isolation(self):
        fake_redis = object()
        storage = RedisStorage(redis=fake_redis)
        isolation = storage.create_isolation()
        assert isinstance(isolation, RedisEventIsolation)
        assert isolation.redis is fake_redis
        assert isolation.key_builder is storage.key_builder
