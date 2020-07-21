import enum
import asyncio
import inspect
import contextvars
from functools import partial
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Dict,
    Generator,
    Generic,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

T = TypeVar("T")
CacheKeyType = Union[str, int]
CacheType = Dict[CacheKeyType, Any]
_RequiredCallback = Callable[
    ..., Union[T, Generator[T, None, None], AsyncGenerator[None, T], Awaitable[T]]
]


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


class Requirement(Generic[T]):
    __slots__ = "callable", "children", "cache_key", "use_cache", "generator_type", "is_async"

    def __init__(
        self,
        callable_: _RequiredCallback[T],
        cache_key: Optional[CacheKeyType] = None,
        use_cache: bool = True,
    ):
        self.callable = callable_
        self.use_cache = use_cache
        self.children: Dict[str, Requirement[Any]] = {}

        self.generator_type = GeneratorKind.not_a_gen

        self.is_async: Optional[bool] = None  # unset value

        if inspect.isasyncgenfunction(callable_):
            self.generator_type = GeneratorKind.async_gen
        elif inspect.isgeneratorfunction(callable_):
            self.generator_type = GeneratorKind.plain_gen
        else:
            self.is_async = inspect.iscoroutinefunction(callable_)

        self.cache_key = hash(callable_) if cache_key is None else cache_key
        self.children = get_reqs_from_callable(callable_)

        assert not (
            set(inspect.signature(callable_).parameters) ^ set(self.children)
        ), "Required can't manage callbacks with non `Requirement` parameters"

    def filter_kwargs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value for key, value in data.items() if key in self.children}

    async def initialize_children(
        self, data: Dict[str, Any], cache_dict: CacheType, stack: AsyncExitStack,
    ) -> None:
        for req_id, req in self.children.items():

            await req.initialize_children(data, cache_dict, stack)

            if req.use_cache and req.cache_key in cache_dict:
                data[req_id] = cache_dict[req.cache_key]

            else:
                data[req_id] = await initialize_callable_requirement(req, data, stack)

            if req.use_cache:
                cache_dict[req.cache_key] = data[req_id]

    async def __call__(
        self, *, cache_dict: CacheType, stack: AsyncExitStack, data: Dict[str, Any],
    ) -> T:
        await self.initialize_children(data, cache_dict, stack)

        if self.use_cache and self.cache_key in cache_dict:
            return cast(T, cache_dict[self.cache_key])
        else:
            result = await initialize_callable_requirement(self, data, stack)
            if self.use_cache:
                cache_dict[self.cache_key] = result

            return result


async def initialize_callable_requirement(
    required: Requirement[T], data: Dict[str, Any], stack: AsyncExitStack
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
        if not required.is_async:
            context = contextvars.copy_context()
            wrapped = partial(context.run, partial(required.callable, **actual_data))

            loop = asyncio.get_event_loop()
            return cast(T, await loop.run_in_executor(None, wrapped))

        else:
            return cast(T, await required.callable(**actual_data))


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
