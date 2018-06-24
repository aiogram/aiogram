import typing

from .filters import AbstractFilter, FilterRecord
from ..handler import Handler


# TODO: provide to set default filters (Like state. It will be always be added to filters set)
# TODO: provide excluding event handlers
# TODO: move check_filter/check_filters functions to FiltersFactory class

class FiltersFactory:
    """
    Default filters factory
    """

    def __init__(self, dispatcher):
        self._dispatcher = dispatcher
        self._registered: typing.List[FilterRecord] = []

    def bind(self, callback: typing.Union[typing.Callable, AbstractFilter],
             validator: typing.Optional[typing.Callable] = None,
             event_handlers: typing.Optional[typing.List[Handler]] = None):
        """
        Register filter

        :param callback: callable or subclass of :obj:`AbstractFilter`
        :param validator: custom validator.
        :param event_handlers: list of instances of :obj:`Handler`
        """
        record = FilterRecord(callback, validator, event_handlers)
        self._registered.append(record)

    def unbind(self, callback: typing.Union[typing.Callable, AbstractFilter]):
        """
        Unregister callback

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
        if custom_filters:
            filters_set.extend(custom_filters)
        if full_config:
            filters_set.extend(self._resolve_registered(self._dispatcher, event_handler,
                                                        {k: v for k, v in full_config.items() if v is not None}))
        return filters_set

    def _resolve_registered(self, dispatcher, event_handler, full_config) -> typing.Generator:
        for record in self._registered:
            if not full_config:
                break

            filter_ = record.resolve(dispatcher, event_handler, full_config)
            if filter_:
                yield filter_

        if full_config:
            raise NameError('Invalid filter name(s): \'' + '\', '.join(full_config.keys()) + '\'')
