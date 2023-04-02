from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Union

if TYPE_CHECKING:
    from aiogram.filters.logic import _InvertFilter


class Filter(ABC):
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

    def __invert__(self) -> "_InvertFilter":
        from aiogram.filters.logic import invert_f

        return invert_f(self)

    def update_handler_flags(self, flags: Dict[str, Any]) -> None:
        """
        Also if you want to extend handler flags with using this filter
        you should implement this method

        :param flags: existing flags, can be updated directly
        """
        pass

    def _signature_to_string(self, *args: Any, **kwargs: Any) -> str:
        items = [repr(arg) for arg in args]
        items.extend([f"{k}={v!r}" for k, v in kwargs.items() if v is not None])

        return f"{type(self).__name__}({', '.join(items)})"

    def __await__(self):  # type: ignore # pragma: no cover
        # Is needed only for inspection and this method is never be called
        return self.__call__
