from itertools import chain
from typing import List, cast

from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.dispatcher.router import Router

INTERNAL_HANDLERS = [
    "update",
    "error",
]


def get_handlers_in_use(
    dispatcher: Dispatcher, handlers_to_skip: List[str] = INTERNAL_HANDLERS
) -> List[str]:
    handlers_in_use: List[str] = []

    for router in [dispatcher.sub_routers, dispatcher]:
        if isinstance(router, list):
            if router:
                handlers_in_use.extend(chain(*list(map(get_handlers_in_use, router))))
        else:
            router = cast(Router, router)
            for update_name, observer in router.observers.items():
                if observer.handlers and update_name not in [*handlers_to_skip, *handlers_in_use]:
                    handlers_in_use.append(update_name)

    return handlers_in_use
