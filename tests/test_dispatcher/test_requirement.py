# todo
from aiogram.dispatcher.requirement import require, CallableRequirement

tick_data = {"ticks": 0}


def test_require():
    x = require(lambda: "str", use_cache=True, cache_key=0)
    assert isinstance(x, CallableRequirement)
    assert callable(x) & callable(x.callable)
    assert x.cache_key == 0
    assert x.use_cache


class TestCallableRequirementCache:
    def test_cache(self):
        ...
