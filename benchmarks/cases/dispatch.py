"""``routing.*``: feed each topology's events through a 3.x Dispatcher, FSM on and off.

One iteration feeds every ``[[event]]`` of the topology once; the results are checked against
``expect`` before timing.
"""

from __future__ import annotations

from typing import Any

from benchmarks.harness import REGISTRY, Corpus, Ctx

_CORPUS = Corpus()


def _routing(input_id: str) -> None:
    variants = _CORPUS.toml(input_id).get("variants", {})

    @REGISTRY.case(input_id, variants=variants)
    def setup(ctx: Ctx) -> Any:
        topology = ctx.toml(input_id)
        updates = {e["update"]: ctx.json(e["update"]) for e in topology["event"]}
        fsm = ctx.variant.get("fsm", "on") == "on"
        feed_all, verify = ctx.adapter.build_dispatch(topology, updates, fsm)
        ctx.run(verify())
        return feed_all


for _entry in _CORPUS.entries.values():
    if _entry["kind"] == "routing":
        _routing(_entry["id"])
