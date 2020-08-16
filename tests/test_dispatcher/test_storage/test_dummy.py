import pytest

from aiogram.dispatcher.storage.dummy import DummyStorage

KFULL_DUMMY_METHODS = {
    "finish",
    "get_data",
    "get_state",
    "reset_data",
    "reset_state",
    "set_data",
    "set_state",
    "update_data",
    # close and wait_closed do not require key
}


WARNING_MESSAGE = (
    "You haven’t set any storage yet so no states and no data will be saved. \n"
    "You can connect MemoryStorage for debug purposes or non-essential data."
)


@pytest.fixture()
def dummy_store():
    return DummyStorage()


@pytest.mark.asyncio
@pytest.mark.parametrize("dummy_method", KFULL_DUMMY_METHODS)
async def test_dummy_storage_warnings(dummy_method: str, dummy_store: DummyStorage):
    with pytest.warns(
        Warning, match=WARNING_MESSAGE,
    ):
        if dummy_method.startswith("get_") or dummy_method in {"finish", "reset_data"}:
            assert await getattr(dummy_store, dummy_method)("42:20") is None
        else:
            assert await getattr(dummy_store, dummy_method)("42:20", None) is None


@pytest.mark.asyncio
async def test_dummy_storage_warnings_for_close(dummy_store: DummyStorage):
    with pytest.warns(Warning, match=WARNING_MESSAGE):
        await dummy_store.close()


@pytest.mark.asyncio
async def test_dummy_storage_warnings_for_wait_closed(dummy_store: DummyStorage):
    with pytest.warns(Warning, match=WARNING_MESSAGE):
        await dummy_store.wait_closed()
