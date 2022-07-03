from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Union

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType, FilterObject


class _LogicFilter:
    __call__: Callable[..., Awaitable[Union[bool, Dict[str, Any]]]]

    def __and__(self, other: "CallbackType") -> "_AndFilter":
        return and_f(self, other)

    def __or__(self, other: "CallbackType") -> "_OrFilter":
        return or_f(self, other)

    def __invert__(self) -> "_InvertFilter":
        return invert_f(self)

    def __await__(self):  # type: ignore # pragma: no cover
        # Is needed only for inspection and this method is never be called
        return self.__call__


class _InvertFilter(_LogicFilter):
    __slots__ = ("target",)

    def __init__(self, target: "FilterObject") -> None:
        self.target = target

    async def __call__(self, *args: Any, **kwargs: Any) -> Union[bool, Dict[str, Any]]:
        return not bool(await self.target.call(*args, **kwargs))


class _AndFilter(_LogicFilter):
    __slots__ = ("targets",)

    def __init__(self, *targets: "FilterObject") -> None:
        self.targets = targets

    async def __call__(self, *args: Any, **kwargs: Any) -> Union[bool, Dict[str, Any]]:
        final_result = {}

        for target in self.targets:
            result = await target.call(*args, **kwargs)
            if not result:
                return False
            if isinstance(result, dict):
                final_result.update(result)

        if final_result:
            return final_result
        return True


class _OrFilter(_LogicFilter):
    __slots__ = ("targets",)

    def __init__(self, *targets: "FilterObject") -> None:
        self.targets = targets

    async def __call__(self, *args: Any, **kwargs: Any) -> Union[bool, Dict[str, Any]]:
        for target in self.targets:
            result = await target.call(*args, **kwargs)
            if not result:
                continue
            if isinstance(result, dict):
                return result
            return bool(result)
        return False


def and_f(target1: "CallbackType", target2: "CallbackType") -> _AndFilter:
    from aiogram.dispatcher.event.handler import FilterObject

    return _AndFilter(FilterObject(target1), FilterObject(target2))


def or_f(target1: "CallbackType", target2: "CallbackType") -> _OrFilter:
    from aiogram.dispatcher.event.handler import FilterObject

    return _OrFilter(FilterObject(target1), FilterObject(target2))


def invert_f(target: "CallbackType") -> _InvertFilter:
    from aiogram.dispatcher.event.handler import FilterObject

    return _InvertFilter(FilterObject(target))
