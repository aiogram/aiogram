import pytest

from aiogram.dispatcher.middlewares import data


def test_exports():
    assert set(data.__all__) == {"AiogramData", "FSMKeysData", "OuterData", "RouterOuterData"}
    assert not hasattr(data, "FSMData")


def test_required_keys():
    # The runtime view must match what mypy sees (a `from __future__` import would make every key required)
    assert data.OuterData.__required_keys__ == {"dispatcher", "bot", "event_context"}
    assert data.RouterOuterData.__required_keys__ == {
        "dispatcher",
        "bot",
        "event_context",
        "event_update",
        "event_router",
    }
    assert data.AiogramData.__required_keys__ == data.RouterOuterData.__required_keys__ | {
        "handler"
    }
    assert data.AiogramData.__optional_keys__ == {
        "bots",
        "fsm_storage",
        "state",
        "raw_state",
        "i18n",
        "i18n_middleware",
    }


def test_middleware_data_is_deprecated_alias():
    with pytest.warns(DeprecationWarning, match="AG4060"):
        from aiogram.dispatcher.middlewares.data import MiddlewareData  # noqa: PLC0415

    assert MiddlewareData is data.AiogramData
