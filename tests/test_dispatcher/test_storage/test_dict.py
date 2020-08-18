from typing import Dict

import pytest

from aiogram.dispatcher.storage.dict import DictStorage


class TestDictStorage:
    def test_init(self):
        storage: DictStorage[Dict[str, str]] = DictStorage()
        assert not storage._data
        assert isinstance(storage._data, dict)

    def test_key_resolution(self):
        storage: DictStorage[Dict[str, str]] = DictStorage()
        key = "L:R"
        assert key not in storage._data
        storage._make_spot_for_key(key)
        assert key in storage._data
        assert storage._data.get(key) == {"state": None, "data": {}}

    @pytest.mark.asyncio
    async def test_get_set_state(self):
        storage: DictStorage[Dict[str, str]] = DictStorage()

        key = "L:R"
        assert await storage.get_state(key=key) is None  # initial state is None

        new_state = "sotm"
        assert await storage.set_state(key=key, state=new_state) is None
        assert await storage.get_state(key=key) == new_state

        assert await storage.reset_state(key=key) is None
        assert await storage.get_state(key=key) is None

    @pytest.mark.asyncio
    async def test_get_set_update_reset_data(self):
        storage: DictStorage[Dict[str, str]] = DictStorage()

        key = "L:R"
        assert await storage.get_data(key=key) == {}  # initial data is empty dict

        new_data = {"sotm": "sotm"}
        assert await storage.set_data(key=key, data=new_data) is None
        assert await storage.get_data(key=key) == new_data

        updated_data = {"mpa": "mpa"}
        assert await storage.update_data(key=key, data=updated_data) is None
        assert await storage.get_data(key=key) == {**new_data, **updated_data}

        assert await storage.reset_data(key=key) is None
        assert await storage.get_data(key=key) == {}  # reset_data makes data empty dict

        new_data = {"abc": "abc"}
        assert await storage.update_data(key=key, data=new_data) is None
        assert await storage.update_data(key=key, data=None) is None
        assert await storage.get_data(key=key) == new_data

    @pytest.mark.asyncio
    async def test_finish(self):
        # finish turns data into initial one
        storage: DictStorage[Dict[str, str]] = DictStorage()

        key = "L:R"
        await storage.set_data(key=key, data={"mpa": "mpa"})
        await storage.set_state(key=key, state="mpa::mpa::mpa::mpa")
        assert await storage.get_data(key=key)
        assert await storage.get_state(key=key)

        assert await storage.finish(key=key) is None
        assert await storage.get_data(key=key) == {}
        assert await storage.get_state(key=key) is None

    @pytest.mark.asyncio
    async def test_close_wait_closed(self):
        storage: DictStorage[Dict[str, str]] = DictStorage()

        storage._data = {"corrupt": "True"}
        assert await storage.close() is None
        assert storage._data == {}
        assert await storage.wait_closed() is None  # noop
