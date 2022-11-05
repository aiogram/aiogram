import abc
import inspect
import typing

from magic_filter import MagicFilter

from ..handler import Handler, FilterObj


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


def get_filter_spec(dispatcher, filter_: callable):
    kwargs = {}
    if not callable(filter_):
        raise TypeError('Filter must be callable and/or awaitable!')

    if isinstance(filter_, MagicFilter):
        filter_ = filter_.resolve

    spec = inspect.getfullargspec(filter_)
    if 'dispatcher' in spec:
        kwargs['dispatcher'] = dispatcher
    if inspect.isawaitable(filter_) \
            or inspect.iscoroutinefunction(filter_) \
            or isinstance(filter_, AbstractFilter):
        return FilterObj(filter=filter_, kwargs=kwargs, is_async=True)
    else:
        return FilterObj(filter=filter_, kwargs=kwargs, is_async=False)


def get_filters_spec(dispatcher, filters: typing.Iterable[callable]):
    data = []
    if filters is not None:
        for i in filters:
            data.append(get_filter_spec(dispatcher, i))
    return data


async def execute_filter(filter_: FilterObj, args):
    """
    Helper for executing filter

    :param filter_:
    :param args:
    :return:
    """
    if filter_.is_async:
        return await filter_.filter(*args, **filter_.kwargs)
    else:
        return filter_.filter(*args, **filter_.kwargs)


async def check_filters(filters: typing.Iterable[FilterObj], args):
    """
    Check list of filters

    :param filters:
    :param args:
    :return:
    """
    data = {}
    if filters is not None:
        for filter_ in filters:
            f = await execute_filter(filter_, args)
            if not f:
                raise FilterNotPassed()
            elif isinstance(f, dict):
                data.update(f)
    return data


class FilterRecord:
    """
    Filters record for factory
    """

    def __init__(self, callback: typing.Union[typing.Callable, 'AbstractFilter'],
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
    Abstract class for custom filters.
    """

    @classmethod
    @abc.abstractmethod
    def validate(cls, full_config: typing.Dict[str, typing.Any]) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """
        Validate and parse config.

        This method will be called by the filters factory when you bind this filter.
        Must be overridden.

        :param full_config: dict with arguments passed to handler registrar
        :return: Current filter config
        """
        pass

    @abc.abstractmethod
    async def check(self, *args) -> bool:
        """
        Will be called when filters checks.

        This method must be overridden.

        :param args:
        :return:
        """
        pass

    async def __call__(self, *args) -> bool:
        return await self.check(*args)

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
    You can make subclasses of that class for custom filters.

    Method ``check`` must be overridden
    """

    @classmethod
    def validate(cls, full_config: typing.Dict[str, typing.Any]) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """
        Here method ``validate`` is optional.
        If you need to use filter from filters factory you need to override this method.

        :param full_config: dict with arguments passed to handler registrar
        :return: Current filter config
        """
        pass


class BoundFilter(Filter):
    """
    To easily create your own filters with one parameter, you can inherit from this filter.

    You need to implement ``__init__`` method with single argument related with key attribute
    and ``check`` method where you need to implement filter logic.
    """

    key = None
    """Unique name of the filter argument. You need to override this attribute."""
    required = False
    """If :obj:`True` this filter will be added to the all of the registered handlers"""
    default = None
    """Default value for configure required filters"""

    @classmethod
    def validate(cls, full_config: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """
        If ``cls.key`` is not :obj:`None` and that is in config returns config with that argument.

        :param full_config:
        :return:
        """
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
        self.targets = [wrap_async(target) for target in targets]

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
        self.targets = [wrap_async(target) for target in targets]

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
