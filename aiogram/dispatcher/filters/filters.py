import abc
import inspect
import typing

from ..handler import Handler
from ...types.base import TelegramObject


class FilterNotPassed(Exception):
    pass


def wrap_async(func):
    async def async_wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    if inspect.isawaitable(func) \
            or inspect.iscoroutinefunction(func) \
            or isinstance(func, AbstractFilter):
        return func
    return async_wrapper


async def check_filter(dispatcher, filter_, args):
    """
    Helper for executing filter

    :param dispatcher:
    :param filter_:
    :param args:
    :return:
    """
    kwargs = {}
    if not callable(filter_):
        raise TypeError('Filter must be callable and/or awaitable!')

    spec = inspect.getfullargspec(filter_)
    if 'dispatcher' in spec:
        kwargs['dispatcher'] = dispatcher
    if inspect.isawaitable(filter_) \
            or inspect.iscoroutinefunction(filter_) \
            or isinstance(filter_, AbstractFilter):
        return await filter_(*args, **kwargs)
    else:
        return filter_(*args, **kwargs)


async def check_filters(dispatcher, filters, args):
    """
    Check list of filters

    :param dispatcher:
    :param filters:
    :param args:
    :return:
    """
    data = {}
    if filters is not None:
        for filter_ in filters:
            f = await check_filter(dispatcher, filter_, args)
            if not f:
                raise FilterNotPassed()
            elif isinstance(f, dict):
                data.update(f)
    return data


class FilterRecord:
    """
    Filters record for factory
    """

    def __init__(self, callback: typing.Callable,
                 validator: typing.Optional[typing.Callable] = None,
                 event_handlers: typing.Optional[typing.Iterable[Handler]] = None,
                 exclude_event_handlers: typing.Optional[typing.Iterable[Handler]] = None):
        if event_handlers and exclude_event_handlers:
            raise ValueError("'event_handlers' and 'exclude_event_handlers' arguments cannot be used together.")

        self.callback = callback
        self.event_handlers = event_handlers
        self.exclude_event_handlers = exclude_event_handlers

        if validator is not None:
            if not callable(validator):
                raise TypeError(f"validator must be callable, not {type(validator)}")
            self.resolver = validator
        elif issubclass(callback, AbstractFilter):
            self.resolver = callback.validate
        else:
            raise RuntimeError('validator is required!')

    def resolve(self, dispatcher, event_handler, full_config):
        if not self._check_event_handler(event_handler):
            return
        config = self.resolver(full_config)
        if config:
            if 'dispatcher' not in config:
                spec = inspect.getfullargspec(self.callback)
                if 'dispatcher' in spec.args:
                    config['dispatcher'] = dispatcher

            for key in config:
                if key in full_config:
                    full_config.pop(key)

            return self.callback(**config)

    def _check_event_handler(self, event_handler) -> bool:
        if self.event_handlers:
            return event_handler in self.event_handlers
        elif self.exclude_event_handlers:
            return event_handler not in self.exclude_event_handlers
        return True


class AbstractFilter(abc.ABC):
    """
    Abstract class for custom filters
    """

    @classmethod
    @abc.abstractmethod
    def validate(cls, full_config: typing.Dict[str, typing.Any]) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """
        Validate and parse config

        :param full_config:
        :return: config
        """
        pass

    @abc.abstractmethod
    async def check(self, *args) -> bool:
        """
        Check object

        :param args:
        :return:
        """
        pass

    async def __call__(self, obj: TelegramObject) -> bool:
        return await self.check(obj)

    def __invert__(self):
        return NotFilter(self)

    def __and__(self, other):
        if isinstance(self, AndFilter):
            self.append(other)
            return self
        return AndFilter(self, other)

    def __or__(self, other):
        if isinstance(self, OrFilter):
            self.append(other)
            return self
        return OrFilter(self, other)


class Filter(AbstractFilter):
    """
    You can make subclasses of that class for custom filters
    """

    @classmethod
    def validate(cls, full_config: typing.Dict[str, typing.Any]) -> typing.Optional[typing.Dict[str, typing.Any]]:
        pass


class BoundFilter(Filter):
    """
    Base class for filters with default validator
    """
    key = None
    required = False
    default = None

    @classmethod
    def validate(cls, full_config: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        if cls.key is not None:
            if cls.key in full_config:
                return {cls.key: full_config[cls.key]}
            elif cls.required:
                return {cls.key: cls.default}


class _LogicFilter(Filter):
    @classmethod
    def validate(cls, full_config: typing.Dict[str, typing.Any]):
        raise ValueError('That filter can\'t be used in filters factory!')


class NotFilter(_LogicFilter):
    def __init__(self, target):
        self.target = wrap_async(target)

    async def check(self, *args):
        return not bool(await self.target(*args))


class AndFilter(_LogicFilter):

    def __init__(self, *targets):
        self.targets = list(wrap_async(target) for target in targets)

    async def check(self, *args):
        """
        All filters must return a positive result

        :param args:
        :return:
        """
        data = {}
        for target in self.targets:
            result = await target(*args)
            if not result:
                return False
            if isinstance(result, dict):
                data.update(result)
        if not data:
            return True
        return data

    def append(self, target):
        self.targets.append(wrap_async(target))


class OrFilter(_LogicFilter):
    def __init__(self, *targets):
        self.targets = list(wrap_async(target) for target in targets)

    async def check(self, *args):
        """
        One of filters must return a positive result

        :param args:
        :return:
        """
        for target in self.targets:
            result = await target(*args)
            if result:
                if isinstance(result, dict):
                    return result
                return True
        return False

    def append(self, target):
        self.targets.append(wrap_async(target))
