from pathlib import Path

import pytest
from _pytest.config import UsageError
from pymongo.errors import InvalidURI, PyMongoError
from pymongo.uri_parser import parse_uri as parse_mongo_url
from redis.asyncio.connection import parse_url as parse_redis_url

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import (
    DisabledEventIsolation,
    MemoryStorage,
    SimpleEventIsolation,
)
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.fsm.storage.redis import RedisEventIsolation, RedisStorage
from tests.mocked_bot import MockedBot

DATA_DIR = Path(__file__).parent / "data"


def pytest_addoption(parser):
    parser.addoption("--redis", default=None, help="run tests which require redis connection")
    parser.addoption("--mongo", default=None, help="run tests which require mongo connection")


def pytest_configure(config):
    config.addinivalue_line("markers", "redis: marked tests require redis connection to run")
    config.addinivalue_line("markers", "mongo: marked tests require mongo connection to run")


def pytest_collection_modifyitems(config, items):
    for db, parse_uri in [("redis", parse_redis_url), ("mongo", parse_mongo_url)]:
        uri = config.getoption(f"--{db}")
        if uri is None:
            skip = pytest.mark.skip(reason=f"need --{db} option with {db} URI to run")
            for item in items:
                if db in item.keywords:
                    item.add_marker(skip)
        else:
            try:
                parse_uri(uri)
            except (ValueError, InvalidURI) as e:
                raise UsageError(f"Invalid {db} URI {uri!r}: {e}")


@pytest.fixture()
def redis_server(request):
    redis_uri = request.config.getoption("--redis")
    return redis_uri


@pytest.fixture()
@pytest.mark.redis
async def redis_storage(redis_server):
    if not redis_server:
        pytest.skip("Redis is not available here")
    storage = RedisStorage.from_url(redis_server)
    try:
        await storage.redis.info()
    except ConnectionError as e:
        pytest.skip(str(e))
    try:
        yield storage
    finally:
        conn = await storage.redis
        await conn.flushdb()
        await storage.close()


@pytest.fixture()
def mongo_server(request):
    mongo_uri = request.config.getoption("--mongo")
    return mongo_uri


@pytest.fixture()
@pytest.mark.mongo
async def mongo_storage(mongo_server):
    if not mongo_server:
        pytest.skip("MongoDB is not available here")
    storage = MongoStorage.from_url(mongo_server)
    try:
        await storage._client.server_info()
    except PyMongoError as e:
        pytest.skip(str(e))
    else:
        yield storage
        await storage._client.drop_database(storage._database)
    finally:
        await storage.close()


@pytest.fixture()
async def memory_storage():
    storage = MemoryStorage()
    try:
        yield storage
    finally:
        await storage.close()


@pytest.fixture()
@pytest.mark.redis
async def redis_isolation(redis_storage):
    isolation = redis_storage.create_isolation()
    return isolation


@pytest.fixture()
async def lock_isolation():
    isolation = SimpleEventIsolation()
    try:
        yield isolation
    finally:
        await isolation.close()


@pytest.fixture()
async def disabled_isolation():
    isolation = DisabledEventIsolation()
    try:
        yield isolation
    finally:
        await isolation.close()


@pytest.fixture()
def bot():
    return MockedBot()


@pytest.fixture()
async def dispatcher():
    dp = Dispatcher()
    await dp.emit_startup()
    try:
        yield dp
    finally:
        await dp.emit_shutdown()
