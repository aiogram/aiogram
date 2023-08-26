from dataclasses import replace
from typing import Any, Dict, List, Optional

from aiogram import loggers
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorageRecord


class HistoryManager:
    def __init__(self, state: FSMContext, destiny: str = "scenes_history", size: int = 10):
        self._size = size
        self._state = state
        self._history_state = FSMContext(
            storage=state.storage, key=replace(state.key, destiny=destiny)
        )

    async def push(self, state: Optional[str], data: Dict[str, Any]) -> None:
        history_data = await self._history_state.get_data()
        history = history_data.setdefault("history", [])
        history.append({"state": state, "data": data})
        if len(history) > self._size:
            history = history[-self._size :]
        loggers.scene.debug("Push state=%s data=%s to history", state, data)

        if not history:
            await self._history_state.set_data({})
        else:
            await self._history_state.update_data(history=history)

    async def pop(self) -> Optional[MemoryStorageRecord]:
        history_data = await self._history_state.get_data()
        history = history_data.setdefault("history", [])
        if not history:
            return None
        record = history.pop()
        state = record["state"]
        data = record["data"]
        if not history:
            await self._history_state.set_data({})
        else:
            await self._history_state.update_data(history=history)
        loggers.scene.debug("Pop state=%s data=%s from history", state, data)
        return MemoryStorageRecord(state=state, data=data)

    async def get(self) -> Optional[MemoryStorageRecord]:
        history_data = await self._history_state.get_data()
        history = history_data.setdefault("history", [])
        if not history:
            return None
        return MemoryStorageRecord(**history[-1])

    async def all(self) -> List[MemoryStorageRecord]:
        history_data = await self._history_state.get_data()
        history = history_data.setdefault("history", [])
        return [MemoryStorageRecord(**item) for item in history]

    async def clear(self) -> None:
        loggers.scene.debug("Clear history")
        await self._history_state.set_data({})

    async def snapshot(self) -> None:
        state = await self._state.get_state()
        data = await self._state.get_data()
        await self.push(state, data)

    async def _set_state(self, state: Optional[str], data: Dict[str, Any]) -> None:
        await self._state.set_state(state)
        await self._state.set_data(data)

    async def rollback(self) -> Optional[str]:
        previous_state = await self.pop()
        if not previous_state:
            await self._set_state(None, {})
            return None

        loggers.scene.debug(
            "Rollback to state=%s data=%s",
            previous_state.state,
            previous_state.data,
        )
        await self._set_state(previous_state.state, previous_state.data)
        return previous_state.state
