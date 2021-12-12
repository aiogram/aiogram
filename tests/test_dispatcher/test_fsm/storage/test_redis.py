from typing import Literal

import pytest

from aiogram.dispatcher.fsm.storage.base import DEFAULT_DESTINY, StorageKey
from aiogram.dispatcher.fsm.storage.redis import DefaultKeyBuilder

pytestmark = pytest.mark.asyncio

PREFIX = "test"
BOT_ID = 42
CHAT_ID = -1
USER_ID = 2
FIELD = "data"


class TestRedisDefaultKeyBuilder:
    @pytest.mark.parametrize(
        "with_bot_id,with_destiny,result",
        [
            [False, False, f"{PREFIX}:{CHAT_ID}:{USER_ID}:{FIELD}"],
            [True, False, f"{PREFIX}:{BOT_ID}:{CHAT_ID}:{USER_ID}:{FIELD}"],
            [True, True, f"{PREFIX}:{BOT_ID}:{CHAT_ID}:{USER_ID}:{DEFAULT_DESTINY}:{FIELD}"],
            [False, True, f"{PREFIX}:{CHAT_ID}:{USER_ID}:{DEFAULT_DESTINY}:{FIELD}"],
        ],
    )
    async def test_generate_key(self, with_bot_id: bool, with_destiny: bool, result: str):
        key_builder = DefaultKeyBuilder(
            prefix=PREFIX,
            with_bot_id=with_bot_id,
            with_destiny=with_destiny,
        )
        key = StorageKey(chat_id=CHAT_ID, user_id=USER_ID, bot_id=BOT_ID, destiny=DEFAULT_DESTINY)
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
