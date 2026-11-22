"""``request.*``: a real HTTP round-trip through ``AiohttpSession`` to a local fake Bot API.

The server runs in the worker's event loop and answers with the pinned ``response.sendMessage``
envelope (wrapped in a list for methods returning lists), so the figure is client + server.
"""

from __future__ import annotations

from typing import Any

from benchmarks.harness import REGISTRY, Corpus, Ctx

_CORPUS = Corpus()
_LIST_METHODS = {"sendMediaGroup"}  # ponytail: the only list-returning method in the corpus


def _request(input_id: str) -> None:
    @REGISTRY.case(input_id, uses=["response.sendMessage"])
    def setup(ctx: Ctx) -> Any:
        adapter = ctx.adapter
        spec = ctx.toml(input_id)
        single = ctx.bytes("response.sendMessage")
        method_name = spec["method"]
        body = adapter.list_envelope(single) if method_name in _LIST_METHODS else single
        base_url, close_server = ctx.run(adapter.fake_api({method_name: body}))
        bot = adapter.api_bot(base_url, spec.get("defaults", {}))
        ctx.on_close(close_server)
        ctx.on_close(bot.session.close)
        method = adapter.build_method(spec, ctx.file)

        async def send() -> None:
            await bot(method)

        return send


for _entry in _CORPUS.entries.values():
    if _entry["kind"] == "request":
        _request(_entry["id"])
