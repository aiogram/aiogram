import aioredis
import pytest
import pytest_asyncio
from pytest_lazyfixture import lazy_fixture
from redis.asyncio.connection import Connection, ConnectionPool

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
    async def test_set_get(self, store):
        assert await store.get_data(chat='1234') == {}
        await store.set_data(chat='1234', data={'foo': 'bar'})
        assert await store.get_data(chat='1234') == {'foo': 'bar'}

    async def test_reset(self, store):
        await store.set_data(chat='1234', data={'foo': 'bar'})
        await store.reset_data(chat='1234')
        assert await store.get_data(chat='1234') == {}

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
    async def test_close_and_open_connection(self, store: RedisStorage2):
        await store.set_data(chat='1234', data={'foo': 'bar'})
        assert await store.get_data(chat='1234') == {'foo': 'bar'}
        await store.close()
        await store.wait_closed()

        pool: ConnectionPool = store._redis.connection_pool

        # noinspection PyUnresolvedReferences
        assert not pool._in_use_connections

        # noinspection PyUnresolvedReferences
        if pool._available_connections:
            # noinspection PyUnresolvedReferences
            connection: Connection = pool._available_connections[0]
            assert connection.is_connected is False

    @pytest.mark.parametrize(
        "chat_id,user_id,state",
        [
            [12345, 54321, "foo"],
            [12345, 54321, None],
            [12345, None, "foo"],
            [None, 54321, "foo"],
        ],
    )
    async def test_set_get_state(self, chat_id, user_id, state, store):
        await store.reset_state(chat=chat_id, user=user_id, with_data=False)

        await store.set_state(chat=chat_id, user=user_id, state=state)
        s = await store.get_state(chat=chat_id, user=user_id)
        assert s == state

    @pytest.mark.parametrize(
        "chat_id,user_id,data,new_data",
        [
            [12345, 54321, {"foo": "bar"}, {"bar": "foo"}],
            [12345, 54321, None, None],
            [12345, 54321, {"foo": "bar"}, None],
            [12345, 54321, None, {"bar": "foo"}],
            [12345, None, {"foo": "bar"}, {"bar": "foo"}],
            [None, 54321, {"foo": "bar"}, {"bar": "foo"}],
        ],
    )
    async def test_set_get_update_data(self, chat_id, user_id, data, new_data, store):
        await store.reset_state(chat=chat_id, user=user_id, with_data=True)

        await store.set_data(chat=chat_id, user=user_id, data=data)
        d = await store.get_data(chat=chat_id, user=user_id)
        assert d == (data or {})

        await store.update_data(chat=chat_id, user=user_id, data=new_data)
        d = await store.get_data(chat=chat_id, user=user_id)
        updated_data = (data or {})
        updated_data.update(new_data or {})
        assert d == updated_data

    async def test_has_bucket(self, store):
        assert store.has_bucket()

    @pytest.mark.parametrize(
        "chat_id,user_id,data,new_data",
        [
            [12345, 54321, {"foo": "bar"}, {"bar": "foo"}],
            [12345, 54321, None, None],
            [12345, 54321, {"foo": "bar"}, None],
            [12345, 54321, None, {"bar": "foo"}],
            [12345, None, {"foo": "bar"}, {"bar": "foo"}],
            [None, 54321, {"foo": "bar"}, {"bar": "foo"}],
        ],
    )
    async def test_set_get_update_bucket(self, chat_id, user_id, data, new_data, store):
        await store.reset_state(chat=chat_id, user=user_id, with_data=True)

        await store.set_bucket(chat=chat_id, user=user_id, bucket=data)
        d = await store.get_bucket(chat=chat_id, user=user_id)
        assert d == (data or {})

        await store.update_bucket(chat=chat_id, user=user_id, bucket=new_data)
        d = await store.get_bucket(chat=chat_id, user=user_id)
        updated_bucket = (data or {})
        updated_bucket.update(new_data or {})
        assert d == updated_bucket
