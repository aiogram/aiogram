from dataclasses import replace, dataclass
from typing import Any, Dict, Optional

from aiogram import loggers
from aiogram.fsm.context import FSMContext


@dataclass
class StateContainer:
    state: str
    data: Dict[str, Any]


class HistoryManager:
    def __init__(self, context: FSMContext, destiny: str = "history", size: int = 10):
        self._size = size
        self._context = context
        self._history_context = FSMContext(
            storage=context.storage, key=replace(context.key, destiny=destiny)
        )

    async def push(self, state: str, data: Dict[str, Any]) -> None:
        history_data = await self._history_context.get_data()
        history = history_data.setdefault("history", [])
        history.append({"state": state, "data": data})
        if len(history) > self._size:
            history = history[-self._size :]
        loggers.scene.debug("Push state=%s data=%s", state, data)
        await self._history_context.update_data(history=history)

    async def pop(self) -> Optional[StateContainer]:
        history_data = await self._history_context.get_data()
        history = history_data.setdefault("history", [])
        if not history:
            return None
        record = history.pop()
        state = record["state"]
        data = record["data"]
        await self._history_context.update_data(history=history)
        loggers.scene.debug("Pop state=%s data=%s", state, data)
        return StateContainer(state=state, data=data)

    async def clear(self):
        loggers.scene.debug("Clear history")
        await self._history_context.clear()

    async def get(self) -> list[StateContainer]:
        history_data = await self._history_context.get_data()
        history = history_data.setdefault("history", [])
        return [StateContainer(**item) for item in history]

    async def snapshot(self) -> None:
        state = await self._context.get_state()
        data = await self._context.get_data()
        await self.push(state, data)

    async def rollback(self) -> Optional[str]:
        state_container = await self.pop()
        if not state_container:
            return None

        state_container = await self.pop()
        if not state_container:
            return None

        loggers.scene.debug(
            "Rollback to state=%s data=%s",
            state_container.state,
            state_container.data,
        )
        await self._context.set_state(state_container.state)
        await self._context.set_data(state_container.data)
        return state_container.state
