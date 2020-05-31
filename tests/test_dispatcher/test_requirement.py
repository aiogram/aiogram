# todo
from aiogram.dispatcher.requirement import Requirement, get_reqs_from_class, get_reqs_from_callable

tick_data = {"ticks": 0}


req1 = Requirement(lambda: 1)
req2 = Requirement(lambda: 1)


async def callback(
    o,
    x=req1,
    y=req2
):
    ...


def test_require():
    x = Requirement(lambda: "str", use_cache=True, cache_key=0)
    assert isinstance(x, Requirement)
    assert callable(x) & callable(x.callable)
    assert x.cache_key == 0
    assert x.use_cache


class TestReqUtils:
    def test_get_reqs_from_callable(self):
        assert set(get_reqs_from_callable(callback).values()) == {req1, req2}
        assert set(get_reqs_from_callable(callback).keys()) == {"x", "y"}

    def test_get_reqs_from_class(self):
        class Class:
            x = req1
            y = req2

        assert set(get_reqs_from_class(Class)) == {"x", "y"}
