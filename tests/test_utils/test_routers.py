from aiogram import Router
from aiogram.utils.routers import find_all_routers, _order_routers


EXPECTED_ROUTERS_NAMES = frozenset({"__init__", "small_module",
                                    "small_package", "nested_small_module"})


def test_all_routers_are_valid():
    routers = find_all_routers("tests.modules_for_tests")
    for router in routers:
        assert isinstance(router, Router)


def test_all_expected_routers_are_found():
    routers = find_all_routers("tests.modules_for_tests")
    found_names = {router.name for router in routers}
    for name in EXPECTED_ROUTERS_NAMES:
        assert name in found_names


def test_routers_ordering():
    indexes = [None, None, None, None, 1, -2, 4]
    routers = [Router(index=index) for index in indexes]
    ordered_indexes = [r.index for r in _order_routers(routers)]
    assert ordered_indexes == [None, 1, None, None, 4, None, -2]

