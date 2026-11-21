"""Decoding: ``update.*`` (model_validate_json + event_type), ``response.*`` (the response path)
and the R04 memory cases."""

from __future__ import annotations

from typing import Any

from benchmarks.harness import REGISTRY, Corpus, Ctx

_ENTRIES = Corpus().entries.values()


def _update(input_id: str) -> None:
    @REGISTRY.case(input_id, memory=True)
    def setup(ctx: Ctx) -> Any:
        raw, decode = ctx.bytes(input_id), ctx.adapter.decode_update
        return lambda: decode(raw)


def _response(input_id: str) -> None:
    @REGISTRY.case(input_id, memory=True)
    def setup(ctx: Ctx) -> Any:
        entry = ctx.entry(input_id)
        content = ctx.bytes(input_id).decode("utf-8")
        decode = ctx.adapter.response_decoder(entry["method"], entry["status"])
        return lambda: decode(content)


# only inputs current 3.x accepts are timed; the rest are oracle inputs (A-07..A-09)
for _entry in _ENTRIES:
    if _entry.get("on_3x") == "ok" and _entry["kind"] == "update":
        _update(_entry["id"])
    elif _entry.get("on_3x") == "ok" and _entry["kind"] == "response":
        _response(_entry["id"])


@REGISTRY.case(
    "memory.update.retained-100k", uses=["update.realistic"], kind="rss", n=100_000, memory=True
)
def retained_updates(ctx: Ctx) -> Any:
    """RSS per retained ``update.realistic``: fresh process, empty baseline subtracted."""
    raw, decode = ctx.bytes("update.realistic"), ctx.adapter.decode_update
    return lambda: decode(raw)


@REGISTRY.case(
    "memory.response.retained-child",
    uses=["response.getUpdates.100"],
    kind="rss",
    n=1_000,
    memory=True,
)
def retained_child(ctx: Ctx) -> Any:
    """RSS per child kept from a 100-update batch, the batch itself dropped."""
    content = ctx.bytes("response.getUpdates.100").decode("utf-8")
    decode = ctx.adapter.response_decoder("getUpdates", 200)
    child = ctx.adapter.retained_child
    return lambda: child(decode(content))


@REGISTRY.case("memory.update.sustained-gc", uses=["update.realistic"], kind="sustained")
def sustained_decode(ctx: Ctx) -> Any:
    """GC on: decode and drop ``update.realistic`` for ``--duration``; throughput + RSS drift."""
    raw, decode = ctx.bytes("update.realistic"), ctx.adapter.decode_update
    return lambda: decode(raw)
