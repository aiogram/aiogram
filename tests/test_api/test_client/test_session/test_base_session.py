import datetime

import pytest

from aiogram.api.client.session.base import BaseSession
from aiogram.api.client.telegram import PRODUCTION, TelegramAPIServer
from aiogram.api.methods import GetMe, Response
from aiogram.utils.mixins import DataMixin


class TestBaseSession(DataMixin):
    def setup(self):
        self["__abstractmethods__"] = BaseSession.__abstractmethods__
        BaseSession.__abstractmethods__ = set()

    def teardown(self):
        BaseSession.__abstractmethods__ = self["__abstractmethods__"]

    def test_init_api(self):
        session = BaseSession()
        assert session.api == PRODUCTION

    def test_init_custom_api(self):
        api = TelegramAPIServer(
            base="http://example.com/{token}/{method}",
            file="http://example.com/{token}/file/{path{",
        )
        session = BaseSession(api=api)
        assert session.api == api

    def test_prepare_value(self):
        session = BaseSession()

        now = datetime.datetime.now()

        assert session.prepare_value("text") == "text"
        assert session.prepare_value(["test"]) == '["test"]'
        assert session.prepare_value({"test": "ok"}) == '{"test": "ok"}'
        assert session.prepare_value(now) == str(round(now.timestamp()))
        assert isinstance(session.prepare_value(datetime.timedelta(minutes=2)), str)
        assert session.prepare_value(42) == "42"

    def test_clean_json(self):
        session = BaseSession()

        cleaned_dict = session.clean_json({"key": "value", "null": None})
        assert "key" in cleaned_dict
        assert "null" not in cleaned_dict

        cleaned_list = session.clean_json(["kaboom", 42, None])
        assert len(cleaned_list) == 2
        assert 42 in cleaned_list
        assert None not in cleaned_list
        assert cleaned_list[0] == "kaboom"

    def test_clean_json_with_nested_json(self):
        session = BaseSession()

        cleaned = session.clean_json(
            {
                "key": "value",
                "null": None,
                "nested_list": ["kaboom", 42, None],
                "nested_dict": {"key": "value", "null": None},
            }
        )

        assert len(cleaned) == 3
        assert "null" not in cleaned

        assert isinstance(cleaned["nested_list"], list)
        assert cleaned["nested_list"] == ["kaboom", 42]

        assert isinstance(cleaned["nested_dict"], dict)
        assert cleaned["nested_dict"] == {"key": "value"}

    def test_clean_json_not_json(self):
        session = BaseSession()

        assert session.clean_json(42) == 42

    def test_raise_for_status(self):
        session = BaseSession()

        session.raise_for_status(Response[bool](ok=True, result=True))
        with pytest.raises(Exception):
            session.raise_for_status(Response[bool](ok=False, description="Error", error_code=400))

    @pytest.mark.asyncio
    async def test_make_request(self):
        session = BaseSession()

        assert await session.make_request("TOKEN", GetMe()) is None
