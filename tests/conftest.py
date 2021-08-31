import aioredis
import pytest
from _pytest.config import UsageError

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


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "redis: marked tests require redis connection to run",
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
        skip_storage = pytest.mark.skip(
            reason="aioredis v2 is not supported by RedisStorage"
        )
        for item in items:
            if "old_storage" in item.keywords:
                item.add_marker(skip_storage)
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
