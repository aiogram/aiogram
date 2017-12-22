from . import Bot
from .. import types
from ..dispatcher import Dispatcher, FSMContext, MODE, UPDATE_OBJECT
from ..utils import context


def _get(key, default=None, no_error=False):
    result = context.get_value(key, default)
    if not no_error and result is None:
        raise RuntimeError(f"Key '{key}' does not exist in the current execution context!\n"
                           f"Maybe asyncio task factory is not configured!\n"
                           f"\t>>> from aiogram.utils import context\n"
                           f"\t>>> loop.set_task_factory(context.task_factory)")
    return result


def get_bot() -> Bot:
    return _get('bot')


def get_dispatcher() -> Dispatcher:
    return _get('dispatcher')


def get_update() -> types.Update:
    return _get(UPDATE_OBJECT)


def get_mode() -> str:
    return _get(MODE, 'unknown')


def get_chat() -> int:
    return _get('chat', no_error=True)


def get_user() -> int:
    return _get('user', no_error=True)


def get_state() -> FSMContext:
    return get_dispatcher().current_state()
