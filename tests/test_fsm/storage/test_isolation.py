import pytest

from aiogram.fsm.storage.base import BaseEventIsolation, StorageKey
from tests.mocked_bot import MockedBot


@pytest.fixture(name="storage_key")
def create_storage_key(bot: MockedBot):
    return StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)


@pytest.mark.parametrize(
    "isolation",
    [
        pytest.lazy_fixture("redis_isolation"),
        pytest.lazy_fixture("lock_isolation"),
        pytest.lazy_fixture("disabled_isolation"),
    ],
)
class TestIsolations:
    @pytest.mark.filterwarnings("ignore::ResourceWarning")
    async def test_lock(
        self,
        isolation: BaseEventIsolation,
        storage_key: StorageKey,
    ):
        async with isolation.lock(key=storage_key):
            assert True, "Are you kidding me?"
