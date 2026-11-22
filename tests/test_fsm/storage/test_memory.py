import asyncio
import copy
import dataclasses
import pickle
import sys
import threading
from types import MappingProxyType

import pytest

from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage, MemoryStorageRecord

THREADS = 4
# A get+set update_data loses about half the keys at this size. Each merge returns a copy of
# the whole record, so the cost is quadratic: 20 000 per thread takes ~15 s.
MERGES_PER_THREAD = 2_000


def make_key(n: int = 0) -> StorageKey:
    return StorageKey(bot_id=42, chat_id=n, user_id=n)


class TestNoRecordOnRead:
    async def test_reads_create_no_records(self):
        storage = MemoryStorage()
        for n in range(100_000):
            key = make_key(n)
            assert await storage.get_state(key) is None
            assert await storage.get_data(key) == {}
            assert await storage.get_value(key, "foo", "baz") == "baz"
        assert len(storage.storage) == 0

    async def test_empty_writes_create_no_records(self):
        storage = MemoryStorage()
        key = make_key()
        await storage.set_state(key, None)
        await storage.set_data(key, {})
        assert await storage.update_data(key, {}) == {}
        assert storage.storage == {}

    async def test_clear_removes_record(self):
        storage = MemoryStorage()
        key = make_key()
        await storage.set_state(key, "state")
        await storage.set_data(key, {"foo": "bar"})
        assert storage.storage == {key: MemoryStorageRecord(state="state", data={"foo": "bar"})}

        await storage.set_state(key, None)
        assert key in storage.storage  # data is still there
        await storage.set_data(key, {})
        assert storage.storage == {}

    async def test_state_without_data_is_kept(self):
        storage = MemoryStorage()
        key = make_key()
        await storage.set_data(key, {"foo": "bar"})
        await storage.set_state(key, "state")
        await storage.set_data(key, {})
        assert storage.storage == {key: MemoryStorageRecord(state="state")}

    async def test_direct_access_to_unknown_key_raises(self):
        with pytest.raises(KeyError):
            MemoryStorage().storage[make_key()]


class TestCopies:
    async def test_update_data_returns_copy(self):
        storage = MemoryStorage()
        key = make_key()
        merged = await storage.update_data(key, {"foo": "bar"})
        merged["spam"] = "eggs"
        assert await storage.get_data(key) == {"foo": "bar"}
        assert merged is not storage.storage[key].data

    async def test_update_data_accepts_any_mapping(self):
        storage = MemoryStorage()
        key = make_key()
        assert await storage.update_data(key, MappingProxyType({"foo": "bar"})) == {"foo": "bar"}
        assert type(storage.storage[key].data) is dict

    async def test_get_data_and_set_data_copy(self):
        storage = MemoryStorage()
        key = make_key()
        data = {"foo": "bar"}
        await storage.set_data(key, data)
        data["spam"] = "eggs"
        got = await storage.get_data(key)
        got["baz"] = 1
        assert storage.storage[key].data == {"foo": "bar"}

    async def test_copies_are_shallow(self):
        # R14 aliasing rule: nested values are shared with the stored record
        storage = MemoryStorage()
        key = make_key()
        await storage.set_data(key, {"items": [1]})
        assert (await storage.get_value(key, "items")) is not storage.storage[key].data["items"]
        assert (await storage.get_data(key))["items"] is storage.storage[key].data["items"]


class TestCopyStorage:
    @pytest.mark.parametrize(
        "clone",
        [copy.deepcopy, lambda storage: pickle.loads(pickle.dumps(storage))],
        ids=["deepcopy", "pickle"],
    )
    async def test_clone_gets_its_own_lock(self, clone):
        storage = MemoryStorage()
        await storage.set_state(make_key(), "state")
        other = clone(storage)
        assert other._lock is not storage._lock
        assert other.storage == storage.storage
        await other.set_state(make_key(), None)
        assert await storage.get_state(make_key()) == "state"


class TestStorageKey:
    def test_slots(self):
        key = make_key()
        assert StorageKey.__slots__
        assert not hasattr(key, "__dict__")
        with pytest.raises(dataclasses.FrozenInstanceError):
            key.chat_id = 1  # type: ignore[misc]

    def test_replace(self):
        key = make_key()
        other = dataclasses.replace(key, destiny="history")
        assert other.destiny == "history"
        assert other.chat_id == key.chat_id
        assert hash(other) != hash(key)


class TestLock:
    async def test_lock_released_when_key_eq_raises(self):
        class BadKey(StorageKey):
            __hash__ = StorageKey.__hash__

            def __eq__(self, other: object) -> bool:
                raise RuntimeError("boom")

        storage = MemoryStorage()
        await storage.set_state(make_key(), "state")
        bad = BadKey(bot_id=42, chat_id=0, user_id=0)  # same hash, so the dict compares keys

        with pytest.raises(RuntimeError, match="boom"):
            await storage.get_state(bad)
        assert not storage._lock.locked()
        assert await storage.get_state(make_key()) == "state"

    def test_threaded_update_data_loses_no_key(self):
        interval = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        storage = MemoryStorage()
        key = make_key()

        async def merge(thread: int) -> None:
            for n in range(MERGES_PER_THREAD):
                await storage.update_data(key, {f"{thread}:{n}": n})

        threads = [
            threading.Thread(target=asyncio.run, args=(merge(thread),))
            for thread in range(THREADS)
        ]
        try:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=120)
            assert not any(thread.is_alive() for thread in threads)
        finally:
            sys.setswitchinterval(interval)

        assert len(storage.storage[key].data) == THREADS * MERGES_PER_THREAD
