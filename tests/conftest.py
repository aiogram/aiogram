import pytest
from _pytest.config import UsageError
from aioredis.connection import parse_url as parse_redis_url

from aiogram import Bot
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.fsm.storage.redis import RedisStorage
from tests.mocked_bot import MockedBot


def pytest_addoption(parser):
    parser.addoption("--redis", default=None, help="run tests which require redis connection")


def pytest_configure(config):
    config.addinivalue_line("markers", "redis: marked tests require redis connection to run")


def pytest_collection_modifyitems(config, items):
    redis_uri = config.getoption("--redis")
    if redis_uri is None:
        skip_redis = pytest.mark.skip(reason="need --redis option with redis URI to run")
        for item in items:
            if "redis" in item.keywords:
                item.add_marker(skip_redis)
        return
    try:
        parse_redis_url(redis_uri)
    except ValueError as e:
        raise UsageError(f"Invalid redis URI {redis_uri!r}: {e}")


@pytest.fixture(scope="session")
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
async def memory_storage():
    storage = MemoryStorage()
    try:
        yield storage
    finally:
        await storage.close()


@pytest.fixture()
def bot():
    bot = MockedBot()
    token = Bot.set_current(bot)
    try:
        yield bot
    finally:
        Bot.reset_current(token)
        bot.me.invalidate(bot)
