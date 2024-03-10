import sys

import pytest

from aiogram.client.default import Default, DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import LinkPreviewOptions


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
