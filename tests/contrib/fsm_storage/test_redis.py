import pytest

from aiogram.contrib.fsm_storage.redis import RedisStorage2


@pytest.fixture()
async def store(redis_options):
    s = RedisStorage2(**redis_options)
    try:
        yield s
    finally:
        conn = await s.redis()
        await conn.flushdb()
        await s.close()
        await s.wait_closed()


@pytest.mark.redis
class TestRedisStorage2:
    @pytest.mark.asyncio
    async def test_set_get(self, store):
        assert await store.get_data(chat='1234') == {}
        await store.set_data(chat='1234', data={'foo': 'bar'})
        assert await store.get_data(chat='1234') == {'foo': 'bar'}

    @pytest.mark.asyncio
    async def test_close_and_open_connection(self, store):
        await store.set_data(chat='1234', data={'foo': 'bar'})
        assert await store.get_data(chat='1234') == {'foo': 'bar'}
        pool_id = id(store._redis)
        await store.close()
        assert await store.get_data(chat='1234') == {'foo': 'bar'}  # new pool was opened at this point
        assert id(store._redis) != pool_id
