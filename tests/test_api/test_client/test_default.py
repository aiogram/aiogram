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

# Field/parameter name -> the ``DefaultBotProperties`` entry it must read from.
# ``disable_notification`` and ``allow_sending_without_reply`` are deliberately absent:
# no generated entity wires a sentinel for them today (the latter is deprecated on
# nearly every send method), so guarding them would only assert a pre-existing gap.
DEFAULT_NAMES = {
    "protect_content": "protect_content",
    "show_caption_above_media": "show_caption_above_media",
    "link_preview_options": "link_preview",
    "disable_web_page_preview": "link_preview_is_disabled",
}

# Entities that legitimately keep a plain ``None`` default.
EXCLUDED_FIELDS = {
    # Incoming payloads: these describe a received message, they are never sent.
    ("Message", "link_preview_options"),
    ("Message", "show_caption_above_media"),
    ("ExternalReplyInfo", "link_preview_options"),
    # Deprecated in favour of ``link_preview_options``, kept only for compatibility.
    ("InputTextMessageContent", "disable_web_page_preview"),
}

# ``Message.send_copy`` intentionally defaults to ``None``: a copy carries the
# already-parsed entities and the original link preview, so no default must apply.
EXCLUDED_METHODS = {("Message", "send_copy")}


def _default_name(name: str) -> str | None:
    if name == "parse_mode" or name.endswith("_parse_mode"):
        return "parse_mode"
    return DEFAULT_NAMES.get(name)


def _telegram_models():
    for module in (methods_module, types_module):
        for name in dir(module):
            obj = getattr(module, name)
            if inspect.isclass(obj) and issubclass(obj, BaseModel):
                yield f"{module.__name__}.{name}", obj


def _default_fields():
    for path, model in _telegram_models():
        for field_name, field in model.model_fields.items():
            default_name = _default_name(field_name)
            if default_name is None:
                continue
            if (model.__name__, field_name) in EXCLUDED_FIELDS:
                continue
            yield f"{path}.{field_name}", field, default_name


def _default_params():
    for path, model in [("aiogram.Bot", Bot), *_telegram_models()]:
        for method_name, method in inspect.getmembers(model, inspect.isfunction):
            if method_name.startswith("_"):
                continue
            if (model.__name__, method_name) in EXCLUDED_METHODS:
                continue
            try:
                signature = inspect.signature(method)
            except (TypeError, ValueError):  # pragma: no cover
                continue
            for param_name, param in signature.parameters.items():
                default_name = _default_name(param_name)
                if default_name is None:
                    continue
                yield f"{path}.{method_name}({param_name})", param, default_name


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


class TestBotDefaultsAreWired:
    """Guards against codegen drift losing a ``Default(...)`` sentinel.

    Without the sentinel a field silently ignores the matching
    ``Bot(default=DefaultBotProperties(...))`` value.
    """

    @pytest.mark.parametrize(
        ("field", "default_name"),
        [pytest.param(field, name, id=path) for path, field, name in _default_fields()],
    )
    def test_model_field_defaults_to_sentinel(self, field, default_name):
        assert field.default == Default(default_name)

    @pytest.mark.parametrize(
        ("param", "default_name"),
        [pytest.param(param, name, id=path) for path, param, name in _default_params()],
    )
    def test_shortcut_param_defaults_to_sentinel(self, param, default_name):
        assert param.default == Default(default_name)
