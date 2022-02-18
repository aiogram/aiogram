from dataclasses import dataclass
from typing import Any, Callable, Optional, Union, cast, overload

from magic_filter import AttrDict

from aiogram.dispatcher.flags.getter import extract_flags_from_object


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
    def __call__(self, value: Callable[..., Any]) -> Callable[..., Any]:  # type: ignore
        pass

    @overload
    def __call__(self, value: Any) -> "FlagDecorator":
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


class FlagGenerator:
    def __getattr__(self, name: str) -> FlagDecorator:
        if name[0] == "_":
            raise AttributeError("Flag name must NOT start with underscore")
        return FlagDecorator(Flag(name, True))
