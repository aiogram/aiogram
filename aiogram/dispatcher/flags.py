from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Union, cast, overload

from magic_filter import AttrDict, MagicFilter

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import HandlerObject


@dataclass(frozen=True)
class Flag:
    name: str
    value: Any


@dataclass(frozen=True)
class FlagDecorator:
    flag: Flag

    @classmethod
    def _with_flag(cls, flag: Flag) -> "FlagDecorator":
        return cls(flag)

    def _with_value(self, value: Any) -> "FlagDecorator":
        new_flag = Flag(self.flag.name, value)
        return self._with_flag(new_flag)

    @overload
    def __call__(self, value: Callable[..., Any], /) -> Callable[..., Any]:  # type: ignore
        pass

    @overload
    def __call__(self, value: Any, /) -> "FlagDecorator":
        pass

    @overload
    def __call__(self, **kwargs: Any) -> "FlagDecorator":
        pass

    def __call__(
        self,
        value: Optional[Any] = None,
        **kwargs: Any,
    ) -> Union[Callable[..., Any], "FlagDecorator"]:
        if value and kwargs:
            raise ValueError("The arguments `value` and **kwargs can not be used together")

        if value is not None and callable(value):
            value.aiogram_flag = {
                **extract_flags_from_object(value),
                self.flag.name: self.flag.value,
            }
            return cast(Callable[..., Any], value)
        return self._with_value(AttrDict(kwargs) if value is None else value)


if TYPE_CHECKING:

    class _ChatActionFlagProtocol(FlagDecorator):
        def __call__(  # type: ignore[override]
            self,
            action: str = ...,
            interval: float = ...,
            initial_sleep: float = ...,
            **kwargs: Any,
        ) -> FlagDecorator:
            pass


class FlagGenerator:
    def __getattr__(self, name: str) -> FlagDecorator:
        if name[0] == "_":
            raise AttributeError("Flag name must NOT start with underscore")
        return FlagDecorator(Flag(name, True))

    if TYPE_CHECKING:
        chat_action: _ChatActionFlagProtocol


def extract_flags_from_object(obj: Any) -> Dict[str, Any]:
    if not hasattr(obj, "aiogram_flag"):
        return {}
    return cast(Dict[str, Any], obj.aiogram_flag)


def extract_flags(handler: Union["HandlerObject", Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract flags from handler or middleware context data

    :param handler: handler object or data
    :return: dictionary with all handler flags
    """
    if isinstance(handler, dict) and "handler" in handler:
        handler = handler["handler"]
    if hasattr(handler, "flags"):
        return handler.flags
    return {}


def get_flag(
    handler: Union["HandlerObject", Dict[str, Any]],
    name: str,
    *,
    default: Optional[Any] = None,
) -> Any:
    """
    Get flag by name

    :param handler: handler object or data
    :param name: name of the flag
    :param default: default value (None)
    :return: value of the flag or default
    """
    flags = extract_flags(handler)
    return flags.get(name, default)


def check_flags(handler: Union["HandlerObject", Dict[str, Any]], magic: MagicFilter) -> Any:
    """
    Check flags via magic filter

    :param handler: handler object or data
    :param magic: instance of the magic
    :return: the result of magic filter check
    """
    flags = extract_flags(handler)
    return magic.resolve(AttrDict(flags))
