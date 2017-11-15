from . import Bot
from .. import types
from ..dispatcher import Dispatcher, FSMContext, MODE, UPDATE_OBJECT
from ..utils import context


def _get(key, default=None, no_error=False):
    result = context.get_value(key, default)
    if not no_error and result is None:
        raise RuntimeError(f"Context is not configured for '{key}'")
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
