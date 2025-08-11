import asyncio
import sys
from pathlib import Path

import pytest
from _pytest.config import UsageError
from pymongo.errors import InvalidURI, PyMongoError
from pymongo.uri_parser import parse_uri as parse_mongo_url
from redis.asyncio.connection import parse_url as parse_redis_url
from redis.exceptions import ConnectionError

from aiogram import Dispatcher
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import (
    DisabledEventIsolation,
    MemoryStorage,
    SimpleEventIsolation,
)
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.fsm.storage.pymongo import PyMongoStorage
from aiogram.fsm.storage.redis import RedisStorage
from tests.mocked_bot import MockedBot

DATA_DIR = Path(__file__).parent / "data"

CHAT_ID = -42
USER_ID = 42

SKIP_MESSAGE_PATTERN = 'Need "--{db}" option with {db} URI to run'
INVALID_URI_PATTERN = "Invalid {db} URI {uri!r}: {err}"


def pytest_addoption(parser):
    parser.addoption("--redis", default=None, help="run tests which require redis connection")
    parser.addoption("--mongo", default=None, help="run tests which require mongo connection")


def pytest_configure(config):
    config.addinivalue_line("markers", "redis: marked tests require redis connection to run")
    config.addinivalue_line("markers", "mongo: marked tests require mongo connection to run")

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    else:
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())


@pytest.fixture()
def redis_server(request):
    redis_uri = request.config.getoption("--redis")
    if redis_uri is None:
        pytest.skip(SKIP_MESSAGE_PATTERN.format(db="redis"))
    else:
        return redis_uri


@pytest.fixture()
async def redis_storage(redis_server):
    try:
        parse_redis_url(redis_server)
    except ValueError as e:
        raise UsageError(INVALID_URI_PATTERN.format(db="redis", uri=redis_server, err=e))
    storage = RedisStorage.from_url(redis_server)
    try:
        await storage.redis.info()
    except ConnectionError as e:
        pytest.fail(str(e))
    try:
        yield storage
    finally:
        conn = await storage.redis
        await conn.flushdb()
        await storage.close()


@pytest.fixture()
def mongo_server(request):
    mongo_uri = request.config.getoption("--mongo")
    if mongo_uri is None:
        pytest.skip(SKIP_MESSAGE_PATTERN.format(db="mongo"))
    else:
        return mongo_uri


@pytest.fixture()
async def mongo_storage(mongo_server):
    try:
        parse_mongo_url(mongo_server)
    except InvalidURI as e:
        raise UsageError(INVALID_URI_PATTERN.format(db="mongo", uri=mongo_server, err=e))
    storage = MongoStorage.from_url(
        url=mongo_server,
        connection_kwargs={"serverSelectionTimeoutMS": 2000},
    )
    try:
        await storage._client.server_info()
    except PyMongoError as e:
        pytest.fail(str(e))
    else:
        yield storage
        await storage._client.drop_database(storage._database)
    finally:
        await storage.close()


@pytest.fixture()
def pymongo_server(request):
    mongo_uri = request.config.getoption("--mongo")
    if mongo_uri is None:
        pytest.skip(SKIP_MESSAGE_PATTERN.format(db="mongo"))
    else:
        return mongo_uri


@pytest.fixture()
async def pymongo_storage(pymongo_server):
    try:
        parse_mongo_url(pymongo_server)
    except InvalidURI as e:
        raise UsageError(INVALID_URI_PATTERN.format(db="mongo", uri=pymongo_server, err=e))
    storage = PyMongoStorage.from_url(
        url=pymongo_server,
        connection_kwargs={"serverSelectionTimeoutMS": 2000},
    )
    try:
        await storage._client.server_info()
    except PyMongoError as e:
        pytest.fail(str(e))
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


@pytest.fixture(name="storage_key")
def create_storage_key(bot: MockedBot):
    return StorageKey(chat_id=CHAT_ID, user_id=USER_ID, bot_id=bot.id)


@pytest.fixture()
async def dispatcher():
    dp = Dispatcher()
    await dp.emit_startup()
    try:
        yield dp
    finally:
        await dp.emit_shutdown()


# @pytest.fixture(scope="session")
# def event_loop_policy(request):
#     if sys.platform == "win32":
#         return asyncio.WindowsSelectorEventLoopPolicy()
#     return asyncio.DefaultEventLoopPolicy()
