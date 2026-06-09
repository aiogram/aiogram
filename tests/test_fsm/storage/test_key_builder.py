from typing import Literal

import pytest

from aiogram.fsm.storage.base import DEFAULT_DESTINY, DefaultKeyBuilder, StorageKey

PREFIX = "test"
BOT_ID = 42
CHAT_ID = -1
USER_ID = 2
THREAD_ID = 3
BUSINESS_CONNECTION_ID = "4"
FIELD = "data"


class TestDefaultKeyBuilder:
    @pytest.mark.parametrize(
        "key_builder,field,result",
        [
            [
                DefaultKeyBuilder(
                    prefix=PREFIX,
                    with_bot_id=True,
                    with_destiny=True,
                    with_business_connection_id=True,
                ),
                FIELD,
                f"{PREFIX}:{BOT_ID}:{BUSINESS_CONNECTION_ID}:{CHAT_ID}:{USER_ID}:{DEFAULT_DESTINY}:{FIELD}",
            ],
            [
                DefaultKeyBuilder(prefix=PREFIX, with_bot_id=True, with_destiny=True),
                None,
                f"{PREFIX}:{BOT_ID}:{CHAT_ID}:{USER_ID}:{DEFAULT_DESTINY}",
            ],
            [
                DefaultKeyBuilder(
                    prefix=PREFIX, with_bot_id=True, with_business_connection_id=True
                ),
                FIELD,
                f"{PREFIX}:{BOT_ID}:{BUSINESS_CONNECTION_ID}:{CHAT_ID}:{USER_ID}:{FIELD}",
            ],
            [
                DefaultKeyBuilder(prefix=PREFIX, with_bot_id=True),
                None,
                f"{PREFIX}:{BOT_ID}:{CHAT_ID}:{USER_ID}",
            ],
            [
                DefaultKeyBuilder(
                    prefix=PREFIX, with_destiny=True, with_business_connection_id=True
                ),
                FIELD,
                f"{PREFIX}:{BUSINESS_CONNECTION_ID}:{CHAT_ID}:{USER_ID}:{DEFAULT_DESTINY}:{FIELD}",
            ],
            [
                DefaultKeyBuilder(prefix=PREFIX, with_destiny=True),
                None,
                f"{PREFIX}:{CHAT_ID}:{USER_ID}:{DEFAULT_DESTINY}",
            ],
            [
                DefaultKeyBuilder(prefix=PREFIX, with_business_connection_id=True),
                FIELD,
                f"{PREFIX}:{BUSINESS_CONNECTION_ID}:{CHAT_ID}:{USER_ID}:{FIELD}",
            ],
            [DefaultKeyBuilder(prefix=PREFIX), None, f"{PREFIX}:{CHAT_ID}:{USER_ID}"],
        ],
    )
    async def test_generate_key(
        self,
        key_builder: DefaultKeyBuilder,
        field: Literal["data", "state", "lock"] | None,
        result: str,
    ):
        key = StorageKey(
            chat_id=CHAT_ID,
            user_id=USER_ID,
            bot_id=BOT_ID,
            business_connection_id=BUSINESS_CONNECTION_ID,
            destiny=DEFAULT_DESTINY,
        )
        assert key_builder.build(key, field) == result

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
