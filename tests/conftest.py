import pytest
from _pytest.config import UsageError
import aioredis.util


def pytest_addoption(parser):
    parser.addoption("--redis", default=None,
                     help="run tests which require redis connection")


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
        address, options = aioredis.util.parse_url(redis_uri)
        assert isinstance(address, tuple), "Only redis and rediss schemas are supported, eg redis://foo."
    except AssertionError as e:
        raise UsageError(f"Invalid redis URI {redis_uri!r}: {e}")


@pytest.fixture(scope='session')
def redis_options(request):
    redis_uri = request.config.getoption("--redis")
    (host, port), options = aioredis.util.parse_url(redis_uri)
    options.update({'host': host, 'port': port})
    return options
