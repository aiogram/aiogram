"""
Need setup task factory:
    >>> from aiogram.utils import context
    >>> loop = asyncio.get_event_loop()
    >>> loop.set_task_factory(context.task_factory)
"""

import asyncio
import typing

CONFIGURED = '@CONFIGURED_TASK_FACTORY'


def task_factory(loop: asyncio.BaseEventLoop, coro: typing.Coroutine):
    """
    Task factory for implementing context processor

    :param loop:
    :param coro:
    :return: new task
    :rtype: :obj:`asyncio.Task`
    """
    # Is not allowed when loop is closed.
    if loop.is_closed():
        raise RuntimeError('Event loop is closed.')

    task = asyncio.Task(coro, loop=loop)

    # Hide factory
    if task._source_traceback:
        del task._source_traceback[-1]

    try:
        task.context = asyncio.Task.current_task().context
    except AttributeError:
        task.context = {CONFIGURED: True}

    return task


def get_current_state() -> typing.Dict:
    """
    Get current execution context from task

    :return: context
    :rtype: :obj:`dict`
    """
    task = asyncio.Task.current_task()
    context = getattr(task, 'context', None)
    if context is None:
        context = task.context = {}
    return context


def get_value(key, default=None):
    """
    Get value from task

    :param key:
    :param default:
    :return: value
    """
    return get_current_state().get(key, default)


def check_value(key):
    """
    Key in context?

    :param key:
    :return:
    """
    return key in get_current_state()


def set_value(key, value):
    """
    Set value

    :param key:
    :param value:
    :return:
    """
    get_current_state()[key] = value


def del_value(key):
    """
    Remove value from context

    :param key:
    :return:
    """
    del get_current_state()[key]


def update_state(data=None, **kwargs):
    """
    Update multiple state items

    :param data:
    :param kwargs:
    :return:
    """
    if data is None:
        data = {}
    state = get_current_state()
    state.update(data, **kwargs)


def check_configured():
    """
    Check loop is configured
    :return:
    """
    return get_value(CONFIGURED)
