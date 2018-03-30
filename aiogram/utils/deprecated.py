"""
Source: https://stackoverflow.com/questions/2536307/decorators-in-the-python-standard-lib-deprecated-specifically
"""

import functools
import inspect
import warnings


def deprecated(reason):
    """
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.
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
                warn_deprecated(msg.format(name=func.__name__, reason=reason))
                warnings.simplefilter('default', DeprecationWarning)
                return func(*args, **kwargs)

            return wrapper

        return decorator

    elif inspect.isclass(reason) or inspect.isfunction(reason):

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
            warn_deprecated(msg1.format(name=func1.__name__))
            return func1(*args, **kwargs)

        return wrapper1

    else:
        raise TypeError(repr(type(reason)))


def warn_deprecated(message, warning=DeprecationWarning, stacklevel=2):
    warnings.simplefilter('always', warning)
    warnings.warn(message, category=warning, stacklevel=stacklevel)
    warnings.simplefilter('default', warning)
