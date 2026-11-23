"""FSM storage and event isolation."""

from __future__ import annotations

from typing import Any

from benchmarks.harness import REGISTRY, Ctx


@REGISTRY.case("fsm.memory.stateless-read")
def stateless_read(ctx: Ctx) -> Any:
    """``get_state`` + ``get_data`` for one key that is never written."""
    ctx.entry("fsm.memory.stateless-read")
    storage, key = ctx.adapter.memory_storage()

    async def read() -> None:
        await storage.get_state(key)
        await storage.get_data(key)

    return read


@REGISTRY.case("isolation.simple.lock")
def isolation_lock(ctx: Ctx) -> Any:
    """Enter and leave the ``SimpleEventIsolation`` lock for one key."""
    ctx.entry("isolation.simple.lock")
    isolation, key = ctx.adapter.event_isolation()

    async def lock() -> None:
        async with isolation.lock(key):
            pass

    return lock
