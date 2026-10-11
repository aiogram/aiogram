from typing import Any

import pytest

from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update, User
from aiogram.utils.i18n import (
    ConstI18nMiddleware,
    FSMI18nMiddleware,
    I18n,
    SimpleI18nMiddleware,
)
from aiogram.utils.i18n.context import get_i18n, gettext, lazy_gettext
from tests.conftest import DATA_DIR
from tests.mocked_bot import MockedBot


def _write_minimal_mo(mo_path, catalog: dict[str, str]) -> None:
    """Write a minimal GNU .mo file so locale dirs can be built on the fly."""
    import struct

    mo_path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted(catalog)
    ids = b""
    strs = b""
    offsets = []
    for key in keys:
        idb = key.encode("utf-8") + b"\x00"
        vb = catalog[key].encode("utf-8") + b"\x00"
        offsets.append((len(ids), len(idb) - 1, len(strs), len(vb) - 1))
        ids += idb
        strs += vb
    num = len(keys)
    key_table_off = 7 * 4
    value_table_off = key_table_off + 8 * num
    keystart = value_table_off + 8 * num
    valuestart = keystart + len(ids)
    output = struct.pack("Iiiiiii", 0x950412DE, 0, num, key_table_off, value_table_off, 0, 0)
    for o1, l1, o2, l2 in offsets:
        output += struct.pack("iiii", l1, keystart + o1, l2, valuestart + o2)
    # gettext requires the last string to end strictly before EOF
    # (real msgfmt pads to alignment), so append trailing padding.
    mo_path.write_bytes(output + ids + strs + b"\x00" * 4)


@pytest.fixture(name="i18n")
def i18n_fixture() -> I18n:
    return I18n(path=DATA_DIR / "locales")


class TestI18nCore:
    def test_init(self, i18n: I18n):
        assert set(i18n.available_locales) == {"en", "uk"}

    def test_init_relative(self):
        i18n_relative = I18n(path="tests/data/locales")
        assert set(i18n_relative.available_locales) == {"en", "uk"}

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
            [None, {"singular": "test"}, "test"],
            [None, {"singular": "test", "locale": "uk"}, "тест"],
            ["en", {"singular": "test", "locale": "uk"}, "тест"],
            ["uk", {"singular": "test", "locale": "uk"}, "тест"],
            ["uk", {"singular": "test"}, "тест"],
            ["it", {"singular": "test"}, "test"],
            [None, {"singular": "test", "n": 2}, "test"],
            [None, {"singular": "test", "n": 2, "locale": "uk"}, "тест"],
            ["en", {"singular": "test", "n": 2, "locale": "uk"}, "тест"],
            ["uk", {"singular": "test", "n": 2, "locale": "uk"}, "тест"],
            ["uk", {"singular": "test", "n": 2}, "тест"],
            ["it", {"singular": "test", "n": 2}, "test"],
            [None, {"singular": "test", "plural": "test2", "n": 2}, "test2"],
            [None, {"singular": "test", "plural": "test2", "n": 2, "locale": "uk"}, "test2"],
            ["en", {"singular": "test", "plural": "test2", "n": 2, "locale": "uk"}, "test2"],
            ["uk", {"singular": "test", "plural": "test2", "n": 2, "locale": "uk"}, "test2"],
            ["uk", {"singular": "test", "plural": "test2", "n": 2}, "test2"],
            ["it", {"singular": "test", "plural": "test2", "n": 2}, "test2"],
        ],
    )
    def test_gettext(self, i18n: I18n, locale: str, case: dict[str, Any], result: str):
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

        assert middleware in dp.message.outer_middleware
        assert middleware in dp.callback_query.outer_middleware

    async def test_setup_exclude(self, i18n: I18n):
        dp = Dispatcher()
        middleware = SimpleI18nMiddleware(i18n=i18n)
        middleware.setup(router=dp, exclude={"message"})

        assert middleware not in dp.update.outer_middleware
        assert middleware not in dp.message.outer_middleware
        assert middleware in dp.callback_query.outer_middleware

    async def test_get_unknown_locale(self, i18n: I18n):
        dp = Dispatcher()
        middleware = SimpleI18nMiddleware(i18n=i18n)
        middleware.setup(router=dp)

        locale = await middleware.get_locale(
            None,
            {
                "event_from_user": User(
                    id=42,
                    is_bot=False,
                    first_name="Test",
                    language_code="unknown",
                )
            },
        )
        assert locale == i18n.default_locale

    async def test_custom_keys(self, i18n: I18n):
        async def handler(event, data):
            return data

        middleware = SimpleI18nMiddleware(
            i18n=i18n, i18n_key="translator", middleware_key="middleware"
        )
        context: dict[str, Any] = await middleware(handler, None, {})
        assert "translator" in context
        assert context["translator"] == i18n
        assert "middleware" in context
        assert context["middleware"] == middleware

    @pytest.mark.parametrize(
        "language_code,expected_locale",
        [
            ("pt-br", "pt_BR"),
            ("pt-BR", "pt_BR"),
            ("pt", "pt"),
            ("uk-UA", "en"),
            ("it-IT", "en"),
            ("unknown", "en"),
            ("zh-hans", "zh_Hans"),
            ("zh-hant", "zh"),
            ("sr-latn", "sr"),
            ("uz-cyrl", "en"),
            ("zh-hans-cn", "zh_CN"),
            ("zh-cn", "zh_CN"),
            ("zh-tw", "zh"),
            ("zh-sg", "zh_Hans"),
            ("en_US", "en"),
            ("pt_BR", "en"),
            pytest.param("", "en", id="empty"),
        ],
    )
    async def test_territory_locale_resolution(self, tmp_path, language_code, expected_locale):
        i18n = I18n(path=tmp_path)
        _write_minimal_mo(
            tmp_path / "pt_BR" / "LC_MESSAGES" / "messages.mo",
            {"test": "teste"},
        )
        _write_minimal_mo(
            tmp_path / "pt" / "LC_MESSAGES" / "messages.mo",
            {"test": "teste-pt"},
        )
        _write_minimal_mo(
            tmp_path / "en" / "LC_MESSAGES" / "messages.mo",
            {"test": "test"},
        )
        _write_minimal_mo(
            tmp_path / "zh" / "LC_MESSAGES" / "messages.mo",
            {"test": "test-zh"},
        )
        _write_minimal_mo(
            tmp_path / "zh_Hans" / "LC_MESSAGES" / "messages.mo",
            {"test": "test-zh-hans"},
        )
        _write_minimal_mo(
            tmp_path / "zh_CN" / "LC_MESSAGES" / "messages.mo",
            {"test": "test-zh-cn"},
        )
        _write_minimal_mo(
            tmp_path / "sr" / "LC_MESSAGES" / "messages.mo",
            {"test": "test-sr"},
        )
        i18n.reload()

        middleware = SimpleI18nMiddleware(i18n=i18n)
        locale = await middleware.get_locale(
            None,
            {
                "event_from_user": User(
                    id=42,
                    is_bot=False,
                    first_name="Test",
                    language_code=language_code,
                )
            },
        )
        assert locale == expected_locale

    @pytest.mark.parametrize(
        "language_code,expected_text",
        [
            ("pt-br", "teste"),
            ("pt", "teste-pt"),
            ("zh-hans", "test-zh"),
            ("zh-cn", "test-zh-cn"),
        ],
    )
    async def test_territory_locale_gettext(self, tmp_path, language_code, expected_text):
        """The resolved territory directory must actually be the one used."""
        i18n = I18n(path=tmp_path)
        _write_minimal_mo(
            tmp_path / "pt_BR" / "LC_MESSAGES" / "messages.mo",
            {"test": "teste"},
        )
        _write_minimal_mo(
            tmp_path / "pt" / "LC_MESSAGES" / "messages.mo",
            {"test": "teste-pt"},
        )
        _write_minimal_mo(
            tmp_path / "zh" / "LC_MESSAGES" / "messages.mo",
            {"test": "test-zh"},
        )
        _write_minimal_mo(
            tmp_path / "zh_CN" / "LC_MESSAGES" / "messages.mo",
            {"test": "test-zh-cn"},
        )
        i18n.reload()

        middleware = SimpleI18nMiddleware(i18n=i18n)

        async def next_call(event, data):
            return gettext("test")

        result = await middleware(
            next_call,
            Update(update_id=42),
            {
                "event_from_user": User(
                    id=42,
                    is_bot=False,
                    first_name="Test",
                    language_code=language_code,
                )
            },
        )
        assert result == expected_text


class TestConstI18nMiddleware:
    async def test_middleware(self, i18n: I18n):
        middleware = ConstI18nMiddleware(i18n=i18n, locale="uk")
        result = await middleware(
            next_call,
            Update(update_id=42),
            {
                "event_from_user": User(
                    id=42, is_bot=False, language_code="it", first_name="Test"
                ),
            },
        )
        assert result == "тест"


class TestFSMI18nMiddleware:
    async def test_middleware(self, i18n: I18n, bot: MockedBot):
        middleware = FSMI18nMiddleware(i18n=i18n)
        storage = MemoryStorage()
        state = FSMContext(storage=storage, key=StorageKey(user_id=42, chat_id=42, bot_id=bot.id))
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

    async def test_without_state(self, i18n: I18n, bot: MockedBot):
        middleware = FSMI18nMiddleware(i18n=i18n)
        data = {
            "event_from_user": User(id=42, is_bot=False, language_code="it", first_name="Test"),
        }
        result = await middleware(next_call, Update(update_id=42), data)
        assert i18n.current_locale == "en"
        assert result == "test"
