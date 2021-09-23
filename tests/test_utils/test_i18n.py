from typing import Any, Dict

import pytest

from aiogram import Dispatcher
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage
from aiogram.types import Update, User
from aiogram.utils.i18n import ConstI18nMiddleware, FSMI18nMiddleware, I18n, SimpleI18nMiddleware
from aiogram.utils.i18n.context import get_i18n, gettext, lazy_gettext
from tests.conftest import DATA_DIR
from tests.mocked_bot import MockedBot


@pytest.fixture(name="i18n")
def i18n_fixture() -> I18n:
    return I18n(path=DATA_DIR / "locales")


class TestI18nCore:
    def test_init(self, i18n: I18n):
        assert set(i18n.available_locales) == {"en", "uk"}

    def test_reload(self, i18n: I18n):
        i18n.reload()
        assert set(i18n.available_locales) == {"en", "uk"}

    def test_current_locale(self, i18n: I18n):
        assert i18n.current_locale == "en"
        i18n.current_locale = "uk"
        assert i18n.current_locale == "uk"
        assert i18n.ctx_locale.get() == "uk"

    def test_use_locale(self, i18n: I18n):
        assert i18n.current_locale == "en"
        with i18n.use_locale("uk"):
            assert i18n.current_locale == "uk"
            with i18n.use_locale("it"):
                assert i18n.current_locale == "it"
            assert i18n.current_locale == "uk"
        assert i18n.current_locale == "en"

    def test_get_i18n(self, i18n: I18n):
        with pytest.raises(LookupError):
            get_i18n()

        with i18n.context():
            assert get_i18n() == i18n

    @pytest.mark.parametrize(
        "locale,case,result",
        [
            [None, dict(singular="test"), "test"],
            [None, dict(singular="test", locale="uk"), "тест"],
            ["en", dict(singular="test", locale="uk"), "тест"],
            ["uk", dict(singular="test", locale="uk"), "тест"],
            ["uk", dict(singular="test"), "тест"],
            ["it", dict(singular="test"), "test"],
            [None, dict(singular="test", n=2), "test"],
            [None, dict(singular="test", n=2, locale="uk"), "тест"],
            ["en", dict(singular="test", n=2, locale="uk"), "тест"],
            ["uk", dict(singular="test", n=2, locale="uk"), "тест"],
            ["uk", dict(singular="test", n=2), "тест"],
            ["it", dict(singular="test", n=2), "test"],
            [None, dict(singular="test", plural="test2", n=2), "test2"],
            [None, dict(singular="test", plural="test2", n=2, locale="uk"), "test2"],
            ["en", dict(singular="test", plural="test2", n=2, locale="uk"), "test2"],
            ["uk", dict(singular="test", plural="test2", n=2, locale="uk"), "test2"],
            ["uk", dict(singular="test", plural="test2", n=2), "test2"],
            ["it", dict(singular="test", plural="test2", n=2), "test2"],
        ],
    )
    def test_gettext(self, i18n: I18n, locale: str, case: Dict[str, Any], result: str):
        if locale is not None:
            i18n.current_locale = locale
        with i18n.context():
            assert i18n.gettext(**case) == result
            assert str(i18n.lazy_gettext(**case)) == result
            assert gettext(**case) == result
            assert str(lazy_gettext(**case)) == result


async def next_call(event, data):
    assert "i18n" in data
    assert "i18n_middleware" in data
    return gettext("test")


@pytest.mark.asyncio
class TestSimpleI18nMiddleware:
    @pytest.mark.parametrize(
        "event_from_user,result",
        [
            [None, "test"],
            [User(id=42, is_bot=False, language_code="uk", first_name="Test"), "тест"],
            [User(id=42, is_bot=False, language_code="it", first_name="Test"), "test"],
        ],
    )
    async def test_middleware(self, i18n: I18n, event_from_user, result):
        middleware = SimpleI18nMiddleware(i18n=i18n)
        result = await middleware(
            next_call,
            Update(update_id=42),
            {"event_from_user": event_from_user},
        )
        assert result == result

    async def test_setup(self, i18n: I18n):
        dp = Dispatcher()
        middleware = SimpleI18nMiddleware(i18n=i18n)
        middleware.setup(router=dp)

        assert middleware not in dp.update.outer_middlewares
        assert middleware in dp.message.outer_middlewares


@pytest.mark.asyncio
class TestConstI18nMiddleware:
    async def test_middleware(self, i18n: I18n):
        middleware = ConstI18nMiddleware(i18n=i18n, locale="uk")
        result = await middleware(
            next_call,
            Update(update_id=42),
            {"event_from_user": User(id=42, is_bot=False, language_code="it", first_name="Test")},
        )
        assert result == "тест"


@pytest.mark.asyncio
class TestFSMI18nMiddleware:
    async def test_middleware(self, i18n: I18n, bot: MockedBot):
        middleware = FSMI18nMiddleware(i18n=i18n)
        storage = MemoryStorage()
        state = FSMContext(bot=bot, storage=storage, user_id=42, chat_id=42)
        data = {
            "event_from_user": User(id=42, is_bot=False, language_code="it", first_name="Test"),
            "state": state,
        }
        result = await middleware(next_call, Update(update_id=42), data)
        assert result == "test"
        await middleware.set_locale(state, "uk")
        assert i18n.current_locale == "uk"
        result = await middleware(next_call, Update(update_id=42), data)
        assert result == "тест"
