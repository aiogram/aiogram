import asyncio
import inspect
import warnings
import functools
from typing import Callable


def deprecated(reason, stacklevel=2) -> Callable:
    """
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.

    Source: https://stackoverflow.com/questions/2536307/decorators-in-the-python-standard-lib-deprecated-specifically
    """

    if isinstance(reason, str):

        # The @deprecated is used with a 'reason'.
        #
        # .. code-block:: python
        #
        #    @deprecated("please, use another function")
        #    def old_function(x, y):
        #      pass

        def decorator(func):

            if inspect.isclass(func):
                msg = "Call to deprecated class {name} ({reason})."
            else:
                msg = "Call to deprecated function {name} ({reason})."

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                warn_deprecated(msg.format(name=func.__name__, reason=reason), stacklevel=stacklevel)
                warnings.simplefilter('default', DeprecationWarning)
                return func(*args, **kwargs)

            return wrapper

        return decorator

    if inspect.isclass(reason) or inspect.isfunction(reason):

        # The @deprecated is used without any 'reason'.
        #
        # .. code-block:: python
        #
        #    @deprecated
        #    def old_function(x, y):
        #      pass

        func1 = reason

        if inspect.isclass(func1):
            msg1 = "Call to deprecated class {name}."
        else:
            msg1 = "Call to deprecated function {name}."

        @functools.wraps(func1)
        def wrapper1(*args, **kwargs):
            warn_deprecated(msg1.format(name=func1.__name__), stacklevel=stacklevel)
            return func1(*args, **kwargs)

        return wrapper1

    raise TypeError(repr(type(reason)))


def warn_deprecated(message, warning=DeprecationWarning, stacklevel=2):
    warnings.simplefilter('always', warning)
    warnings.warn(message, category=warning, stacklevel=stacklevel)
    warnings.simplefilter('default', warning)


def renamed_argument(old_name: str, new_name: str, until_version: str, stacklevel: int = 3):
    """
    A meta-decorator to mark an argument as deprecated.

    .. code-block:: python3

        @renamed_argument("chat", "chat_id", "3.0")  # stacklevel=3 by default
        @renamed_argument("user", "user_id", "3.0", stacklevel=4)
        def some_function(user_id, chat_id=None):
            print(f"user_id={user_id}, chat_id={chat_id}")

        some_function(user=123)  #  prints 'user_id=123, chat_id=None' with warning
        some_function(123)  #  prints 'user_id=123, chat_id=None' without warning
        some_function(user_id=123)  #  prints 'user_id=123, chat_id=None' without warning


    :param old_name:
    :param new_name:
    :param until_version: the version in which the argument is scheduled to be removed
    :param stacklevel: leave it to default if it's the first decorator used.
    Increment with any new decorator used.
    :return: decorator
    """

    def decorator(func):
        is_coroutine = asyncio.iscoroutinefunction(func)

        def _handling(kwargs):
            """
            Returns updated version of kwargs.
            """
            routine_type = 'coroutine' if is_coroutine else 'function'
            if old_name in kwargs:
                warn_deprecated(f"In {routine_type} '{func.__name__}' argument '{old_name}' "
                                f"is renamed to '{new_name}' "
                                f"and will be removed in aiogram {until_version}",
                                stacklevel=stacklevel)
                kwargs = kwargs.copy()
                kwargs.update({new_name: kwargs.pop(old_name)})
            return kwargs

        if is_coroutine:
            @functools.wraps(func)
            async def wrapped(*args, **kwargs):
                kwargs = _handling(kwargs)
                return await func(*args, **kwargs)
        else:
            @functools.wraps(func)
            def wrapped(*args, **kwargs):
                kwargs = _handling(kwargs)
                return func(*args, **kwargs)

        return wrapped

    return decorator
