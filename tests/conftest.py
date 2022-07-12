import asyncio

import aioredis
import pytest
from _pytest.config import UsageError
from motor.motor_asyncio import AsyncIOMotorClient
from yarl import URL

from aiogram import Bot
from . import TOKEN

try:
    import aioredis.util
except ImportError:
    pass


def pytest_addoption(parser):
    parser.addoption(
        "--redis",
        default=None,
        help="run tests which require redis connection",
    )
    parser.addoption(
        "--mongo",
        default=None,
        help=(
            "run tests which require mongo connection, e.g.: "
            "mongodb://test:qwerty@127.0.0.1:27017/test_db?authSource=admin"
        ),
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "redis: marked tests require redis connection to run",
    )
    config.addinivalue_line(
        "markers",
        "mongo: marked tests require mongo connection to run",
    )


def pytest_collection_modifyitems(config, items):
    redis_uri = config.getoption("--redis")
    if redis_uri is None:
        skip_redis = pytest.mark.skip(
            reason="need --redis option with redis URI to run"
        )
        for item in items:
            if "redis" in item.keywords:
                item.add_marker(skip_redis)
        return

    redis_version = int(aioredis.__version__.split(".")[0])
    options = None
    if redis_version == 1:
        (host, port), options = aioredis.util.parse_url(redis_uri)
        options.update({'host': host, 'port': port})
    elif redis_version == 2:
        try:
            options = aioredis.connection.parse_url(redis_uri)
        except ValueError as e:
            raise UsageError(f"Invalid redis URI {redis_uri!r}: {e}")

    try:
        assert isinstance(options, dict), \
            "Only redis and rediss schemas are supported, eg redis://foo."
    except AssertionError as e:
        raise UsageError(f"Invalid redis URI {redis_uri!r}: {e}")


@pytest.fixture(scope='session')
def redis_options(request):
    redis_uri = request.config.getoption("--redis")
    if redis_uri is None:
        pytest.skip("need --redis option with redis URI to run")
        return

    redis_version = int(aioredis.__version__.split(".")[0])
    if redis_version == 1:
        (host, port), options = aioredis.util.parse_url(redis_uri)
        options.update({'host': host, 'port': port})
        return options

    if redis_version == 2:
        try:
            return aioredis.connection.parse_url(redis_uri)
        except ValueError as e:
            raise UsageError(f"Invalid redis URI {redis_uri!r}: {e}")

    raise UsageError("Unsupported aioredis version")


@pytest.fixture(scope='session')
def mongo_options(request):
    mongo_uri = request.config.getoption("--mongo")
    if mongo_uri is None:
        pytest.skip("need --mongo option with mongo URI to run")
        return

    mongo_client = AsyncIOMotorClient(mongo_uri)
    db_name = mongo_client.get_default_database().name
    # MongoDB URI-s are pretty much standard URLs so we can use yarl.URL() on them
    url = URL(mongo_uri)
    host, port = url.host, url.port
    options = {
        'host': host,
        'port': port,
        'db_name': db_name,
        'uri': mongo_uri,
    }
    return options


@pytest.fixture(name='bot')
async def bot_fixture():
    """Bot fixture."""
    bot = Bot(TOKEN)
    yield bot
    session = await bot.get_session()
    if session and not session.closed:
        await session.close()
        await asyncio.sleep(0.2)
