from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Union

from pydantic import BaseModel


class BaseFilter(ABC, BaseModel):
    """
    If you want to register own filters like builtin filters you will need to write subclass
    of this class with overriding the :code:`__call__`
    method and adding filter attributes.

    BaseFilter is subclass of :class:`pydantic.BaseModel` that's mean all subclasses of BaseFilter has
    the validators based on class attributes and custom validator.
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

    def __await__(self):  # type: ignore # pragma: no cover
        # Is needed only for inspection and this method is never be called
        return self.__call__
