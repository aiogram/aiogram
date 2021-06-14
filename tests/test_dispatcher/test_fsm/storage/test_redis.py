import pytest

from aiogram.dispatcher.fsm.storage.redis import RedisStorage
from tests.mocked_bot import MockedBot


@pytest.mark.redis
class TestRedisStorage:
    @pytest.mark.parametrize(
        "prefix_bot,result",
        [
            [False, "fsm:-1:2"],
            [True, "fsm:42:-1:2"],
            [{42: "kaboom"}, "fsm:kaboom:-1:2"],
            [lambda bot: "kaboom", "fsm:kaboom:-1:2"],
        ],
    )
    @pytest.mark.asyncio
    async def test_generate_key(self, bot: MockedBot, redis_server, prefix_bot, result):
        storage = RedisStorage.from_url(redis_server, prefix_bot=prefix_bot)
        assert storage.generate_key(bot, -1, 2) == result
