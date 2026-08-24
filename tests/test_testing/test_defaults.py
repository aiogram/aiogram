from typing import Any

import pytest

from aiogram.client.default import Default, DefaultBotProperties
from aiogram.methods.base import TelegramMethod
from aiogram.test import Blueprint, build_environment
from aiogram.test.defaults import resolve_defaults
from aiogram.test.synthesis import SynthesisContext, synthesize
from aiogram.types import Chat, InputMediaPhoto

from .test_synthesis import all_methods

DEFAULTS = DefaultBotProperties(
    parse_mode="HTML",
    protect_content=True,
    disable_notification=True,
    link_preview_is_disabled=True,
    show_caption_above_media=True,
)


def methods_with_default_fields() -> list[tuple[type[TelegramMethod[Any]], str]]:
    return [
        (method, name)
        for method in all_methods()
        for name, info in method.model_fields.items()
        if isinstance(info.default, Default)
    ]


@pytest.fixture
def environment():
    env = build_environment(Blueprint(default=DEFAULTS))
    try:
        yield env
    finally:
        env.dispose_sync()


class TestResolveDefaults:
    def test_sentinel_is_replaced(self, environment):
        assert resolve_defaults(Default("parse_mode"), environment.bot) == "HTML"

    def test_plain_values_are_untouched(self, environment):
        assert resolve_defaults("MarkdownV2", environment.bot) == "MarkdownV2"
        assert resolve_defaults(None, environment.bot) is None

    def test_containers_are_walked(self, environment):
        resolved = resolve_defaults(
            {"items": [Default("parse_mode")], "pair": (Default("parse_mode"),)},
            environment.bot,
        )

        assert resolved == {"items": ["HTML"], "pair": ("HTML",)}

    def test_nested_models_are_resolved(self, environment):
        media = InputMediaPhoto(media="file-id")

        resolved = resolve_defaults(media, environment.bot)

        assert resolved.parse_mode == "HTML"
        assert media.parse_mode == Default("parse_mode")

    def test_model_without_defaults_is_returned_as_is(self, environment):
        chat = Chat(id=42, type="private")

        assert resolve_defaults(chat, environment.bot) is chat


class TestAgreesWithPrepareValue:
    """
    Typed resolution must agree with the framework's own serialization-time resolution
    (:meth:`aiogram.client.session.base.BaseSession.prepare_value`). The toolkit needs a
    second implementation because a fake session never serializes — this guard is what
    keeps the two from drifting apart, in the spirit of ``TestParseModeDefaultIsWired``.
    """

    @pytest.mark.parametrize(
        ("method", "field"),
        methods_with_default_fields(),
        ids=lambda item: item.__name__ if isinstance(item, type) else str(item),
    )
    def test_every_default_bearing_field(self, environment, method, field):
        instance = synthesize(method, SynthesisContext())
        session = environment.session
        bot = environment.bot

        resolved = resolve_defaults(instance, bot)

        assert session.prepare_value(getattr(resolved, field), bot=bot, files={}) == (
            session.prepare_value(getattr(instance, field), bot=bot, files={})
        )
