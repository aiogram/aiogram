import contextlib
from collections import Mapping

import pytest

from aiogram.dispatcher.state.context import CurrentUserContext, _default_key_maker
from aiogram.dispatcher.storage.dict import DictStorage

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock, patch  # type: ignore


@pytest.fixture(scope="function")
def storage() -> DictStorage:
    return DictStorage()


@contextlib.contextmanager
def patch_dict_storage_method(method: str):
    with patch(
        f"aiogram.dispatcher.storage.dict.DictStorage.{method}", new_callable=CoroutineMock,
    ) as mocked:
        yield mocked


def test_default_key_maker():
    chat_id, user_id = None, None
    with pytest.raises(ValueError):
        _default_key_maker(chat_id, user_id)

    chat_id, user_id = 1, None
    assert _default_key_maker(chat_id, user_id) == f"{chat_id}:{chat_id}"

    chat_id, user_id = None, 1
    assert _default_key_maker(chat_id, user_id) == f"{user_id}:{user_id}"

    chat_id, user_id = 2 ** 8, 2 ** 10
    assert _default_key_maker(chat_id, user_id) == f"{chat_id}:{user_id}"


class TestCurrentUserContext:
    def test_init(self, storage):
        chat_id, user_id = 1, 2
        ctx = CurrentUserContext(storage, chat_id, user_id)
        assert not hasattr(ctx, "__dict__")
        assert ctx.storage == storage
        assert ctx.key == _default_key_maker(chat_id, user_id)

    def test_custom_key_maker(self, storage):
        key_maker_const_result = "mpa"

        def my_key_maker(chat_id: int, user_id: int):
            return key_maker_const_result

        chat_id, user_id = 1, 2
        ctx = CurrentUserContext(storage, chat_id, user_id, key_maker=my_key_maker)
        assert ctx.key == my_key_maker(chat_id, user_id) == key_maker_const_result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("setter_method", ("set_state", "set_data"))
    async def test_setters(self, storage, setter_method):
        chat_id, user_id = 1, 2
        ctx = CurrentUserContext(storage, chat_id, user_id)

        with patch_dict_storage_method(setter_method) as mocked:
            await getattr(ctx, setter_method)("some")
            mocked.assert_awaited()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("getter_method", ("set_state", "set_data"))
    async def test_getters(self, storage, getter_method):
        chat_id, user_id = 1, 2
        ctx = CurrentUserContext(storage, chat_id, user_id)

        with patch_dict_storage_method(getter_method) as mocked:
            await getattr(ctx, getter_method)()
            mocked.assert_awaited()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("reseter_method", ("reset_data", "reset_state", "finish"))
    async def test_setters(self, storage, reseter_method):
        chat_id, user_id = 1, 2
        ctx = CurrentUserContext(storage, chat_id, user_id)

        with patch_dict_storage_method(reseter_method) as mocked:
            await getattr(ctx, reseter_method)()
            mocked.assert_awaited()

    @pytest.mark.asyncio
    async def test_update_data(self, storage):
        chat_id, user_id = 1, 2
        ctx = CurrentUserContext(storage, chat_id, user_id)

        with patch_dict_storage_method("update_data") as mocked:
            await ctx.update_data()
            mocked.assert_awaited()

        with pytest.raises(
            ValueError,
            match="type for `data` is expected to be a subtype of `collections.Mapping`",
        ):
            await ctx.update_data(data="definetely not mapping")

        class LegitMapping(Mapping):
            def __getitem__(self, k):
                return "value"

            def __len__(self):
                return 1

            def __iter__(self):
                yield "key"

        new_data = LegitMapping()
        assert await ctx.update_data(data=new_data) is None
        assert await ctx.get_data() == new_data
