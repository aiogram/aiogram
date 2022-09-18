import aioredis
import pytest
import pytest_asyncio
from pytest_lazyfixture import lazy_fixture

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage, RedisStorage2


@pytest_asyncio.fixture()
@pytest.mark.redis
async def redis_store(redis_options):
    if int(aioredis.__version__.split(".")[0]) == 2:
        pytest.skip('aioredis v2 is not supported.')
        return
    s = RedisStorage(**redis_options)
    try:
        yield s
    finally:
        conn = await s.redis()
        await conn.execute('FLUSHDB')
        await s.close()
        await s.wait_closed()


@pytest_asyncio.fixture()
@pytest.mark.redis
async def redis_store2(redis_options):
    s = RedisStorage2(**redis_options)
    try:
        yield s
    finally:
        conn = await s.redis()
        await conn.flushdb()
        await s.close()
        await s.wait_closed()


@pytest_asyncio.fixture()
async def memory_store():
    yield MemoryStorage()


@pytest.mark.parametrize(
    "store", [
        lazy_fixture('redis_store'),
        lazy_fixture('redis_store2'),
        lazy_fixture('memory_store'),
    ]
)
class TestStorage:
    @pytest.mark.asyncio
    async def test_set_get(self, store):
        assert await store.get_data(chat='1234') == {}
        await store.set_data(chat='1234', data={'foo': 'bar'})
        assert await store.get_data(chat='1234') == {'foo': 'bar'}

    @pytest.mark.asyncio
    async def test_reset(self, store):
        await store.set_data(chat='1234', data={'foo': 'bar'})
        await store.reset_data(chat='1234')
        assert await store.get_data(chat='1234') == {}

    @pytest.mark.asyncio
    async def test_reset_empty(self, store):
        await store.reset_data(chat='1234')
        assert await store.get_data(chat='1234') == {}


@pytest.mark.parametrize(
    "store", [
        lazy_fixture('redis_store'),
        lazy_fixture('redis_store2'),
    ]
)
class TestRedisStorage2:
    @pytest.mark.asyncio
    async def test_close_and_open_connection(self, store):
        await store.set_data(chat='1234', data={'foo': 'bar'})
        assert await store.get_data(chat='1234') == {'foo': 'bar'}
        pool_id = id(store._redis)
        await store.close()
        await store.wait_closed()

        # new pool will be open at this point
        assert await store.get_data(chat='1234') == {
            'foo': 'bar',
        }
        assert id(store._redis) != pool_id
