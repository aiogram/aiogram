import asyncio
import pytest

from aiogram.utils.lockmanager import LockManager, CantDeleteWithWaiters


@pytest.fixture()
def storage_data():
    return {}


def test_lock_manager_without_context_add_lock(storage_data):
    lock_manager = LockManager(storage_data)
    lock_manager.get_lock(key="test")
    assert lock_manager.storage_data
    assert "test" in lock_manager.storage_data


@pytest.mark.asyncio
async def test_lock_manager_with_context(storage_data):
    lock_manager = LockManager(storage_data, key="test")
    locks_acquire_result = []
    expected = [False, True, False]

    locks_acquire_result.append(bool(lock_manager.storage_data))
    async with lock_manager:
        assert "test" in lock_manager.storage_data
        locks_acquire_result.append(bool(lock_manager.storage_data))
    locks_acquire_result.append(bool(lock_manager.storage_data))
    assert locks_acquire_result == expected


@pytest.mark.asyncio
async def test_lock_manager_raise_waiters_exc(storage_data):
    async def task(lock_manager):
        async with lock_manager:
            await asyncio.sleep(0.1)

    async def task2(lock_manager):
        async with lock_manager:
            await asyncio.sleep(0.1)

    async def task_del(lock_manager):
        await asyncio.sleep(0.05)
        with pytest.raises(CantDeleteWithWaiters):
            lock_manager.del_lock("test")

    lock_manager = LockManager(storage_data, key="test")
    await asyncio.gather(task(lock_manager), task2(lock_manager), task_del(lock_manager))


@pytest.mark.asyncio
async def test_lock_manager_log_miss_key(caplog, storage_data):
    lock_manager = LockManager(storage_data)
    lock_manager.del_lock("test")
    assert "Can`t find Lock by key to delete" in caplog.text


@pytest.mark.asyncio
async def test_lock_manager_release_first(storage_data):
    lock_manager = LockManager(storage_data, key="test")
    with pytest.raises(RuntimeError):
        lock_manager.release()

    assert not lock_manager.storage_data
