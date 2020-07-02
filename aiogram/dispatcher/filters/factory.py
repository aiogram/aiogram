import typing

from .filters import AbstractFilter, FilterRecord
from ..handler import Handler


class FiltersFactory:
    """
    Filters factory
    """

    def __init__(self, dispatcher):
        self._dispatcher = dispatcher
        self._registered: typing.List[FilterRecord] = []

    def bind(self, callback: typing.Union[typing.Callable, AbstractFilter],
             validator: typing.Optional[typing.Callable] = None,
             event_handlers: typing.Optional[typing.List[Handler]] = None,
             exclude_event_handlers: typing.Optional[typing.Iterable[Handler]] = None):
        """
        Register filter

        :param callback: callable or subclass of :obj:`AbstractFilter`
        :param validator: custom validator.
        :param event_handlers: list of instances of :obj:`Handler`
        :param exclude_event_handlers: list of excluded event handlers (:obj:`Handler`)
        """
        record = FilterRecord(callback, validator, event_handlers, exclude_event_handlers)
        self._registered.append(record)

    def unbind(self, callback: typing.Union[typing.Callable, AbstractFilter]):
        """
        Unregister filter

        :param callback: callable of subclass of :obj:`AbstractFilter`
        """
        for record in self._registered:
            if record.callback == callback:
                self._registered.remove(record)

    def resolve(self, event_handler, *custom_filters, **full_config
                ) -> typing.List[typing.Union[typing.Callable, AbstractFilter]]:
        """
        Resolve filters to filters-set

        :param event_handler:
        :param custom_filters:
        :param full_config:
        :return:
        """
        filters_set = []
        filters_set.extend(self._resolve_registered(event_handler,
                                                    {k: v for k, v in full_config.items() if v is not None}))
        if custom_filters:
            filters_set.extend(custom_filters)

        return filters_set

    def _resolve_registered(self, event_handler, full_config) -> typing.Generator:
        """
        Resolve registered filters

        :param event_handler:
        :param full_config:
        :return:
        """
        for record in self._registered:
            filter_ = record.resolve(self._dispatcher, event_handler, full_config)
            if filter_:
                yield filter_

        if full_config:
            raise NameError("Invalid filter name(s): '" + "', ".join(full_config.keys()) + "'")
