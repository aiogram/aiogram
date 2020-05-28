import abc
import enum
import inspect
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Dict,
    Generic,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

T = TypeVar("T")
CacheKeyType = Union[str, int]
_RequiredCallback = Callable[..., Union[T, AsyncGenerator[None, T], Awaitable[T]]]


class GeneratorKind(enum.IntEnum):
    not_a_gen = enum.auto()  # not a generator
    plain_gen = enum.auto()  # proper generator not async
    async_gen = enum.auto()  # async generator


@asynccontextmanager
async def move_to_async_gen(context_manager: Any) -> Any:
    """
    Wrap existing contextmanager into a asynchronous generator, then async ctx manager
    """
    try:
        yield context_manager.__enter__()
    except Exception as e:
        err = context_manager.__exit__(type(e), e, None)
        if not err:
            raise e
    else:
        context_manager.__exit__(None, None, None)


class Requirement(abc.ABC, Generic[T]):
    """
    Interface for all requirements
    """

    async def __call__(
        self, cache_dict: Dict[CacheKeyType, Any], stack: AsyncExitStack, data: Dict[str, Any],
    ) -> T:
        raise NotImplementedError()


class CallableRequirement(Requirement[T]):
    __slots__ = "callable", "children", "cache_key", "use_cache", "generator_type"

    def __init__(
        self,
        callable_: _RequiredCallback[T],
        *,
        cache_key: Optional[CacheKeyType] = None,
        use_cache: bool = True,
    ):
        self.callable = callable_
        self.generator_type = GeneratorKind.not_a_gen

        if inspect.isasyncgenfunction(callable_):
            self.generator_type = GeneratorKind.async_gen
        elif inspect.isgeneratorfunction(callable_):
            self.generator_type = GeneratorKind.plain_gen

        self.cache_key = hash(callable_) if cache_key is None else cache_key
        self.use_cache = use_cache
        self.children = get_reqs_from_callable(callable_)

        assert not (
            set(inspect.signature(callable_).parameters) ^ set(self.children)
        ), "Required can't manage callbacks with non `Requirement` parameters"

    def filter_kwargs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value for key, value in data.items() if key in self.children}

    async def initialize_children(
        self, data: Dict[str, Any], cache_dict: Dict[CacheKeyType, Any], stack: AsyncExitStack
    ) -> None:
        for req_id, req in self.children.items():
            if isinstance(req, CachedRequirement):
                data[req_id] = await req(data=data, cache_dict=cache_dict, stack=stack)
                continue

            if isinstance(req, CallableRequirement):
                await req.initialize_children(data, cache_dict, stack)

                if req.use_cache and req.cache_key in cache_dict:
                    data[req_id] = cache_dict[req.cache_key]

                else:
                    data[req_id] = await initialize_callable_requirement(req, data, stack)

                if req.use_cache:
                    cache_dict[req.cache_key] = data[req_id]

    async def __call__(
        self, cache_dict: Dict[CacheKeyType, Any], stack: AsyncExitStack, data: Dict[str, Any],
    ) -> T:
        await self.initialize_children(data, cache_dict, stack)

        if self.use_cache and self.cache_key in cache_dict:
            return cast(T, cache_dict[self.cache_key])
        else:
            result = await initialize_callable_requirement(self, data, stack)
            if self.use_cache:
                cache_dict[self.cache_key] = result
            return result


class CachedRequirement(Requirement[T]):
    __slots__ = "cache_key", "value_on_miss"

    def __init__(self, cache_key: CacheKeyType, value_on_miss: T):
        self.cache_key: CacheKeyType = cache_key
        self.value_on_miss = value_on_miss

    async def __call__(
        self, cache_dict: Dict[CacheKeyType, Any], stack: AsyncExitStack, data: Dict[str, Any],
    ) -> T:
        return cache_dict.get(self.cache_key, self.value_on_miss)


async def initialize_callable_requirement(
    required: CallableRequirement[T], data: Dict[str, Any], stack: AsyncExitStack
) -> T:
    actual_data = required.filter_kwargs(data)
    async_cm: Optional[Any] = None

    if required.generator_type is GeneratorKind.async_gen:
        async_cm = asynccontextmanager(required.callable)(**actual_data)  # type: ignore
    elif required.generator_type is GeneratorKind.plain_gen:
        async_cm = move_to_async_gen(contextmanager(required.callable)(**actual_data))  # type: ignore

    if async_cm is not None:
        return await stack.enter_async_context(async_cm)
    else:
        result = required.callable(**actual_data)
        if isinstance(result, Awaitable):
            return cast(T, await result)
        return cast(T, result)


def get_reqs_from_callable(callable_: _RequiredCallback[T]) -> Dict[str, Requirement[Any]]:
    signature = inspect.signature(callable_)
    return {
        param_name: param_self.default
        for param_name, param_self in signature.parameters.items()
        if isinstance(param_self.default, Requirement)
    }


def get_reqs_from_class(cls: Type[Any]) -> Dict[str, Requirement[Any]]:
    return {
        req_attr: req for req_attr, req in cls.__dict__.items() if isinstance(req, Requirement)
    }


def require(
    what: _RequiredCallback[T],
    *,
    cache_key: Optional[CacheKeyType] = None,
    use_cache: bool = True,
) -> T:
    return CallableRequirement(what, cache_key=cache_key, use_cache=use_cache)  # type: ignore
