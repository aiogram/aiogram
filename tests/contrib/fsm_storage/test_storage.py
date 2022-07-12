import aioredis
import pytest
from pytest_lazyfixture import lazy_fixture
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage, RedisStorage2
from aiogram.contrib.fsm_storage.mongo import MongoStorage, DEFAULT_DB_NAME


@pytest.fixture()
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


@pytest.fixture()
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


@pytest.fixture()
async def memory_store():
    yield MemoryStorage()


@pytest.fixture()
@pytest.mark.mongo
async def mongo_store(mongo_options):
    yield MongoStorage(uri=mongo_options['uri'], db_from_uri=True)


@pytest.mark.parametrize(
    "store", [
        lazy_fixture('redis_store'),
        lazy_fixture('redis_store2'),
        lazy_fixture('memory_store'),
        lazy_fixture('mongo_store'),
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
        assert await store.get_data(chat='1234') == {
            'foo': 'bar'}  # new pool was opened at this point
        assert id(store._redis) != pool_id


@pytest.mark.asyncio
@pytest.mark.mongo
async def test_mongo_dbname_from_uri(mongo_options):
    """
    Check that it is possible to use the db_name provided in the URI
    without specifying it as a separate parameter.
    """

    mongo_uri = mongo_options['uri']

    default_db_name = DEFAULT_DB_NAME
    uri_db_name = mongo_options['db_name']
    assert uri_db_name in mongo_uri
    assert default_db_name not in mongo_uri

    # Make two instances - one with the parameter, and the other - without
    mongo_store_1 = MongoStorage(uri=mongo_options['uri'])
    mongo_store_2 = MongoStorage(uri=mongo_options['uri'], db_from_uri=True)

    db_1 = await mongo_store_1.get_db()
    db_2 = await mongo_store_2.get_db()

    assert db_1.name == default_db_name
    assert db_2.name == uri_db_name
