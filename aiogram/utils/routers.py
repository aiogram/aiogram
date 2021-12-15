from typing import Set, List

from aiogram import Router
from aiogram.utils.imports import DEFAULT_EXCLUDE_MODULES, import_all_modules


def find_all_routers(
    root: str,
    order_by_index: bool = True,
    package: str = None,
    exclude_modules: Set[str] = DEFAULT_EXCLUDE_MODULES
) -> List[Router]:
    """
    if order_by_index is True: routers are ordered by index applying following rules:
        - indexes as in list: 0, 1, 2, ... -3, -2, -1
        - if index is None - it is going between positive and negative numbers, also filling in
            empty slots in positives, ordered as was ordered in WeakSet
            ex.: 0, None, 2, None, 5, None, -1
            ex.: 0, 1, 2, 3, 4, 5, None, -1
            ex.: 0, 1, 2, 3, 4, 5, None, None, -3, -1

    :param root: root directory where function will start importing and digging to subdirectories
    :param order_by_index:
    :param package: your top-level package name if 'root' is not absolute (starts with .)
    :param exclude_modules: set of names that will be ignored,
        if it is a directory - also doesn't iterate over its insides
    """
    import_all_modules(root, package, exclude_modules)
    routers = list(Router.get_instances())
    return routers if order_by_index is False else _order_routers(routers)


def _order_routers(routers: 'List[Router]') -> List[Router]:
    unordered = []
    ordered_routers = {}
    negative_ordered_routers = []
    checked_indexes = {}
    for router in routers:
        if router.index is None:
            unordered.append(router)
            continue
        if router.index < 0:
            negative_ordered_routers.append(router)
        else:
            ordered_routers[router.index] = router

        if router.index in checked_indexes:
            raise ValueError(f"Views {checked_indexes[router.index]} and {router} have equal indexes!")
        checked_indexes[router.index] = router

    result = []
    for i in range(len(routers) - len(negative_ordered_routers)):
        ordered = ordered_routers.pop(i, None)
        if ordered is not None:
            result.append(ordered)
            continue
        if unordered:
            result.append(unordered.pop(0))

    # for case where there is a router with an index too big (more than the amount of routers)
    result += sorted(ordered_routers.values(), key=lambda x: x.index)

    result += sorted(negative_ordered_routers, key=lambda x: x.index)
    return result
