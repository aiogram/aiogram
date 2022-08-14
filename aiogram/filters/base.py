from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Union

from aiogram.filters.logic import _LogicFilter


class Filter(_LogicFilter, ABC):
    """
    If you want to register own filters like builtin filters you will need to write subclass
    of this class with overriding the :code:`__call__`
    method and adding filter attributes.
    """

    if TYPE_CHECKING:
        # This checking type-hint is needed because mypy checks validity of overrides and raises:
        # error: Signature of "__call__" incompatible with supertype "BaseFilter"  [override]
        # https://mypy.readthedocs.io/en/latest/error_code_list.html#check-validity-of-overrides-override
        __call__: Callable[..., Awaitable[Union[bool, Dict[str, Any]]]]
    else:  # pragma: no cover

        @abstractmethod
        async def __call__(self, *args: Any, **kwargs: Any) -> Union[bool, Dict[str, Any]]:
            """
            This method should be overridden.

            Accepts incoming event and should return boolean or dict.

            :return: :class:`bool` or :class:`Dict[str, Any]`
            """
            pass

    def update_handler_flags(self, flags: Dict[str, Any]) -> None:
        pass

    def _signature_to_string(self, *args: Any, **kwargs: Any) -> str:
        items = [repr(arg) for arg in args]
        items.extend([f"{k}={v!r}" for k, v in kwargs.items()])

        return f"{type(self).__name__}({', '.join(items)})"

    def __str__(self) -> str:
        return self._signature_to_string()


BaseFilter = Filter
