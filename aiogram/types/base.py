import sys
import threading
from collections.abc import Callable
from typing import Any
from unittest.mock import sentinel

from pydantic import BaseModel, ConfigDict, GetCoreSchemaHandler
from pydantic_core import CoreSchema

from aiogram.client.context_controller import BotContextController
from aiogram.client.default import Default


def _fail_fast_lists(schema: Any, model: type[BaseModel]) -> None:
    """
    Make every list of the model's own core schema stop at the first invalid item.

    Otherwise pydantic keeps one error per item, each with the full location, so rejecting
    a nested update costs items x depth. Nested models are skipped: their own schema
    goes through this hook as well.
    """
    if isinstance(schema, dict):
        if schema.get("type") == "model" and schema.get("cls") is not model:
            return
        if schema.get("type") == "list":
            schema["fail_fast"] = True
        for value in schema.values():
            _fail_fast_lists(value, model)
    elif isinstance(schema, list):
        for value in schema:
            _fail_fast_lists(value, model)


_building = threading.local()


def _own(model: type[BaseModel]) -> bool:
    return model.__module__.startswith("aiogram.")


def rebuild_in_module(
    model: type[BaseModel],
    rebuild: Callable[..., bool | None],
    force: bool,
    raise_errors: bool,
    parent_namespace_depth: int,
    types_namespace: Any,
) -> bool | None:
    """
    ``model_rebuild`` of aiogram's own models: resolve in the defining module, never in a frame.

    Pydantic resolves a deferred model in the frame of whoever uses it first, so a local name
    there (``Chat = ...``) would shadow aiogram's and stay in the schema for good. The module
    has every name it needs: :mod:`aiogram.types` puts them there.
    """
    if types_namespace is None and _own(model):
        types_namespace = vars(sys.modules[model.__module__])
    models: set[type[BaseModel]] = _building.__dict__.setdefault("models", set())
    nested = model in models
    models.add(model)
    try:
        return rebuild(
            force=force,
            raise_errors=raise_errors,
            # this function and the caller's model_rebuild sit between pydantic and the frame
            _parent_namespace_depth=parent_namespace_depth + 2,
            _types_namespace=types_namespace,
        )
    finally:
        if not nested:
            models.discard(model)


class TelegramObject(BotContextController, BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        extra="allow",
        validate_assignment=True,
        frozen=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        defer_build=True,
        protected_namespaces=(),
    )

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: type[BaseModel],
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        if (
            source is cls
            and _own(cls)
            and not cls.__pydantic_complete__
            and not _building.__dict__.get("models")
        ):
            # Nested in a model that is not aiogram's (a user model, a TypeAdapter): build it
            # alone first, in its own module, so it does not resolve its fields in the namespace
            # of the outer model. Inside aiogram's own builds the namespace is already right.
            cls.model_rebuild()
        schema = handler(source)
        _fail_fast_lists(schema, source)
        return schema

    @classmethod
    def model_rebuild(
        cls,
        *,
        force: bool = False,
        raise_errors: bool = True,
        _parent_namespace_depth: int = 2,
        _types_namespace: Any = None,
    ) -> bool | None:
        return rebuild_in_module(
            cls,
            super().model_rebuild,
            force,
            raise_errors,
            _parent_namespace_depth,
            _types_namespace,
        )

    def __init_subclass__(cls, **kwargs: Any) -> None:
        # Runs before pydantic collects the fields. A subclass copies the fields of a built base,
        # and otherwise resolves them again in its own module, which lacks the names aiogram.types
        # imports only under TYPE_CHECKING: build its bases first (a no-op for built ones).
        if not cls.__module__.startswith("aiogram.types."):
            for base in cls.__mro__[1:]:
                if issubclass(base, TelegramObject) and _own(base):
                    base.model_rebuild()
        super().__init_subclass__(**kwargs)


class MutableTelegramObject(TelegramObject):
    model_config = ConfigDict(
        frozen=False,
    )


# special sentinel object which used in a situation when None might be a useful value
UNSET: Any = sentinel.UNSET
UNSET_TYPE: Any = type(UNSET)

# Unused constants are needed only for backward compatibility with external
# libraries that a working with framework internals
UNSET_PARSE_MODE: Any = Default("parse_mode")
UNSET_DISABLE_WEB_PAGE_PREVIEW: Any = Default("link_preview_is_disabled")
UNSET_PROTECT_CONTENT: Any = Default("protect_content")
