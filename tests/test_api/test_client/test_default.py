import inspect
import sys

import pytest
from pydantic import BaseModel

from aiogram import Bot
from aiogram import methods as methods_module
from aiogram import types as types_module
from aiogram.client.default import Default, DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import LinkPreviewOptions


def _is_parse_mode(name: str) -> bool:
    return name == "parse_mode" or name.endswith("_parse_mode")


def _telegram_models():
    for module in (methods_module, types_module):
        for name in dir(module):
            obj = getattr(module, name)
            if inspect.isclass(obj) and issubclass(obj, BaseModel):
                yield f"{module.__name__}.{name}", obj


def _parse_mode_fields():
    for path, model in _telegram_models():
        for field_name, field in model.model_fields.items():
            if _is_parse_mode(field_name):
                yield f"{path}.{field_name}", field


def _parse_mode_params():
    # ``Message.send_copy`` intentionally defaults to ``None``: a copy carries the
    # already-parsed entities, so no parse mode must be applied.
    excluded = {("Message", "send_copy")}

    for path, model in [("aiogram.Bot", Bot), *_telegram_models()]:
        for method_name, method in inspect.getmembers(model, inspect.isfunction):
            if method_name.startswith("_"):
                continue
            if (model.__name__, method_name) in excluded:
                continue
            try:
                signature = inspect.signature(method)
            except (TypeError, ValueError):  # pragma: no cover
                continue
            for param_name, param in signature.parameters.items():
                if _is_parse_mode(param_name):
                    yield f"{path}.{method_name}({param_name})", param


class TestDefault:
    def test_init(self):
        default = Default("test")
        assert default._name == "test"

    def test_name_property(self):
        default = Default("test")
        assert default.name == "test"

    def test_str(self):
        default = Default("test")
        assert str(default) == "Default('test')"

    def test_repr(self):
        default = Default("test")
        assert repr(default) == "<Default('test')>"

    def test_eq_same_name(self):
        assert Default("test") == Default("test")

    def test_eq_different_name(self):
        assert Default("foo") != Default("bar")

    def test_hash(self):
        assert hash(Default("test")) == hash(Default("test"))


class TestDefaultBotProperties:
    def test_post_init_empty(self):
        default_bot_properties = DefaultBotProperties()

        assert default_bot_properties.link_preview is None

    def test_post_init_auto_fill_link_preview(self):
        default_bot_properties = DefaultBotProperties(
            link_preview_is_disabled=True,
            link_preview_prefer_small_media=True,
            link_preview_prefer_large_media=True,
            link_preview_show_above_text=True,
        )

        assert default_bot_properties.link_preview == LinkPreviewOptions(
            is_disabled=True,
            prefer_small_media=True,
            prefer_large_media=True,
            show_above_text=True,
        )

    def test_getitem(self):
        default_bot_properties = DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
            link_preview_prefer_small_media=True,
            link_preview_prefer_large_media=True,
            link_preview_show_above_text=True,
        )

        assert default_bot_properties["parse_mode"] == ParseMode.HTML
        assert default_bot_properties["link_preview_is_disabled"] is True
        assert default_bot_properties["link_preview_prefer_small_media"] is True
        assert default_bot_properties["link_preview_prefer_large_media"] is True
        assert default_bot_properties["link_preview_show_above_text"] is True

    @pytest.mark.skipif(sys.version_info < (3, 12), reason="requires python3.11 or higher")
    def test_dataclass_creation_3_10_plus(self):
        params = DefaultBotProperties.__dataclass_params__
        assert params.slots is True
        assert params.kw_only is True


class TestParseModeDefaultIsWired:
    """Guards against codegen drift losing the ``Default("parse_mode")`` sentinel.

    Without the sentinel a field silently ignores
    ``Bot(default=DefaultBotProperties(parse_mode=...))``.
    """

    @pytest.mark.parametrize(
        "field",
        [pytest.param(field, id=path) for path, field in _parse_mode_fields()],
    )
    def test_model_field_defaults_to_sentinel(self, field):
        assert field.default == Default("parse_mode")

    @pytest.mark.parametrize(
        "param",
        [pytest.param(param, id=path) for path, param in _parse_mode_params()],
    )
    def test_shortcut_param_defaults_to_sentinel(self, param):
        assert param.default == Default("parse_mode")
