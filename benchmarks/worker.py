"""The measuring side: runs cases in one warm process.

``run`` drives a Worker in-process. ``compare`` starts one worker per side as
``<side python> -I <copy>/benchmarks/worker.py`` and talks JSON lines over stdin/stdout, so the
side's installed aiogram is imported and the repository root never shadows it.

``worker.py --rss <case> <variant-json> <n>`` is the fresh-subprocess RSS probe: it builds the
case, retains ``n`` objects and prints one JSON reading.
"""

from __future__ import annotations

if __name__ == "__main__":  # started by path with -I: make the copied package importable
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import gc
import inspect
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from benchmarks import memory
from benchmarks.harness import (
    REGISTRY,
    Case,
    Corpus,
    Ctx,
    Registry,
    Settings,
    calibrate,
    gc_off,
    make_timer,
    process_env,
)


def new_loop(name: str) -> tuple[str, asyncio.AbstractEventLoop]:
    if name in {"auto", "uvloop"}:
        try:
            import uvloop
        except ImportError:
            if name == "uvloop":
                raise
        else:
            return "uvloop", uvloop.new_event_loop()
    return "asyncio", asyncio.new_event_loop()


def load_adapter() -> Any:
    from benchmarks.adapters import load

    return load()


class Worker:
    def __init__(self, registry: Registry | None = None, corpus: Corpus | None = None) -> None:
        if registry is None:
            import benchmarks.cases  # noqa: F401  registers every case into REGISTRY

            registry = REGISTRY
        self.registry = registry
        self.corpus = corpus or Corpus()
        self.settings = Settings()
        self.loop_name, self.loop = "asyncio", None
        self.adapter: Any = None
        self._reset()

    def _reset(self) -> None:
        self.case: Case | None = None
        self.ctx: Ctx | None = None
        self.body: Any = None
        self.timer: Any = None
        self.loops = 0
        self.warmed = False
        self.last_rss: dict[str, Any] | None = None

    # -- protocol operations -------------------------------------------------------------------

    def op_init(self, settings: dict[str, Any]) -> dict[str, Any]:
        self.settings = Settings(**settings)
        self.loop_name, self.loop = new_loop(self.settings.loop)
        asyncio.set_event_loop(self.loop)
        self.adapter = load_adapter()
        return process_env(self.loop_name, self.corpus)

    def op_close(self) -> None:
        if self.loop is not None:
            self.loop.close()
            asyncio.set_event_loop(None)
            self.loop = None

    def op_cases(self) -> dict[str, list[dict[str, str]]]:
        return {case_id: case.expand() for case_id, case in self.registry.items()}

    def op_prepare(self, case: str, variant: dict[str, str]) -> dict[str, Any]:
        self._reset()
        if case not in self.registry:
            return {"status": "missing"}
        self.case = self.registry[case]
        self.ctx = Ctx(self.corpus, self.adapter, self.loop, variant)
        self.body = self.case.setup(self.ctx)
        fixtures = [self.ctx.fixtures[i] for i in sorted(self.ctx.fixtures)]
        if self.case.kind == "rss":  # sampled in fresh subprocesses; warm for tracemalloc only
            for _ in range(self.settings.warmup):
                self.body()
            self.warmed = True
            return {
                "status": "ok",
                "kind": "rss",
                "unit": "B",
                "loops": self.case.n,
                "fixtures": fixtures,
            }
        self.timer = make_timer(self.body, self.loop)
        self.timer(self.settings.warmup)  # the "20 real calls first" rule; B-02 asserts on it
        self.warmed = True
        if self.case.kind == "sustained" or self.settings.gc:
            return {
                "status": "ok",
                "kind": "sustained",
                "unit": "us",
                "loops": 0,
                "fixtures": fixtures,
            }
        self.loops = calibrate(self.timer, self.settings.min_sample_s)
        return {
            "status": "ok",
            "kind": "time",
            "unit": "us",
            "loops": self.loops,
            "fixtures": fixtures,
        }

    def op_sample(self) -> float:
        assert self.case is not None and self.warmed, "sample before warm-up"
        if self.case.kind == "rss":
            return self._rss_sample()
        return gc_off(lambda: self.timer(self.loops)) / self.loops * 1e6

    def op_sustained(self) -> dict[str, Any]:
        """GC on, loop for ``duration_s``: one throughput sample and RSS reading per interval."""
        assert self.case is not None and self.warmed, "sample before warm-up"
        gc.enable()
        end = time.perf_counter() + self.settings.duration_s
        samples, series = [], []
        source = None
        interval = self.settings.interval_s
        batch = 1  # calls between clock checks: about 1/20 of an interval once known
        while time.perf_counter() < end:
            iterations, started = 0, time.perf_counter()
            while (elapsed := time.perf_counter() - started) < interval:
                self.timer(batch)
                iterations += batch
                if elapsed < interval / 20:
                    batch *= 2
            samples.append(elapsed / iterations * 1e6)
            batch = max(1, iterations // 20)
            reading = memory.rss()
            source = reading["source"]
            series.append(memory.rss_value(reading))
        known = [v for v in series if v is not None]
        drift = (known[-1] - known[0]) / known[0] if len(known) > 1 and known[0] else None
        return {
            "samples": samples,
            "sustained": {
                "duration_s": self.settings.duration_s,
                "interval_s": self.settings.interval_s,
                "rss": series,
                "rss_source": source,
                "rss_drift": drift,
            },
        }

    def op_finish(self) -> dict[str, Any]:
        """Per-case extras (tracemalloc, last RSS probe), then the case's cleanups."""
        assert self.case is not None and self.ctx is not None
        extra: dict[str, Any] = {}
        if self.case.memory:
            call = self.body
            if inspect.iscoroutinefunction(self.body):
                call = lambda: self.loop.run_until_complete(self.body())  # noqa: E731
            extra["memory"] = {"tracemalloc": memory.traced(call)}
        if self.last_rss is not None:
            extra["memory"] = {**extra.get("memory", {}), "rss": self.last_rss}
        for cleanup in reversed(self.ctx.cleanups):
            result = cleanup()
            if asyncio.iscoroutine(result):
                self.loop.run_until_complete(result)
        self._reset()
        return extra

    # -- fresh-subprocess RSS ------------------------------------------------------------------

    def _rss_sample(self) -> float:
        """(RSS with n retained objects - RSS with none) / n, each from a fresh subprocess."""
        assert self.case is not None and self.ctx is not None
        variant = json.dumps(self.ctx.variant)
        args = [sys.executable, "-I", __file__, "--rss", self.case.id, variant]
        settings = json.dumps(asdict(self.settings))
        readings = []
        for n in (0, self.case.n):
            out = subprocess.run(
                [*args, str(n), settings], capture_output=True, text=True, check=True
            )
            readings.append(json.loads(out.stdout))
        base, full = readings
        self.last_rss = {"n": self.case.n, "source": full["source"], "empty": base, "full": full}
        if memory.rss_value(full) is None:
            return float("nan")
        return (memory.rss_value(full) - memory.rss_value(base)) / self.case.n


def rss_child(case_id: str, variant: dict[str, str], n: int, settings: dict[str, Any]) -> None:
    worker = Worker()
    worker.op_init(settings)
    case = worker.registry[case_id]
    produce = case.setup(Ctx(worker.corpus, worker.adapter, worker.loop, variant))
    produce()  # same imports and lazy initialisation in the empty baseline
    retained = [produce() for _ in range(n)]
    gc.collect()
    reading = memory.rss()
    sys.stdout.write(json.dumps(reading) + "\n")
    del retained


def serve() -> None:
    out = os.fdopen(os.dup(1), "w", encoding="utf-8")
    os.dup2(2, 1)  # anything a case prints goes to stderr, not into the protocol
    worker = Worker()
    for line in sys.stdin:
        msg = json.loads(line)
        try:
            reply = {"ok": getattr(worker, f"op_{msg['op']}")(**msg.get("args", {}))}
        except Exception as e:  # noqa: BLE001  reported to the driver, which stops the run
            reply = {"error": f"{type(e).__name__}: {e}"}
        out.write(json.dumps(reply) + "\n")
        out.flush()


if __name__ == "__main__":
    if sys.argv[1:2] == ["--rss"]:
        rss_child(sys.argv[2], json.loads(sys.argv[3]), int(sys.argv[4]), json.loads(sys.argv[5]))
    else:
        serve()
