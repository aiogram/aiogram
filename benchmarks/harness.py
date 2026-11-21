"""Benchmark harness core: corpus access, case registry, timing, statistics, environment, schema.

Method (v4/plans/A-contracts/A-05-bench-harness.md): a warm process, 20 warm-up calls, GC off,
loops calibrated to >= 0.2 s per sample, 7 samples, median / IQR / p5 / p95 plus every raw sample.
"""

from __future__ import annotations

import functools
import gc
import hashlib
import inspect
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import sysconfig
import time
import tomllib
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = 1
PACKAGE = Path(__file__).resolve().parent
CORPUS = PACKAGE / "corpus"


# ---------------------------------------------------------------------------------------------
# Settings and corpus
# ---------------------------------------------------------------------------------------------


@dataclass
class Settings:
    repeats: int = 7
    warmup: int = 20
    min_sample_s: float = 0.2
    gc: bool = False  # False: GC off while sampling; True: sustained GC-on mode
    duration_s: float = 30.0
    interval_s: float = 1.0
    loop: str = "auto"  # auto (uvloop when importable) | asyncio | uvloop


class Corpus:
    """Reads pinned inputs by A-04 id and checks each file against its manifest sha256."""

    def __init__(self, root: Path = CORPUS) -> None:
        self.root = root
        manifest = root / "MANIFEST.toml"
        self.manifest_sha256 = hashlib.sha256(manifest.read_bytes()).hexdigest()
        self.entries = {e["id"]: e for e in tomllib.loads(manifest.read_text("utf-8"))["input"]}

    def entry(self, input_id: str) -> dict[str, Any]:
        return self.entries[input_id]

    def bytes(self, input_id: str) -> bytes:
        entry = self.entries[input_id]
        data = (self.root / entry["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            msg = f"{input_id}: file does not match its MANIFEST.toml sha256"
            raise ValueError(msg)
        return data

    def json(self, input_id: str) -> Any:
        return json.loads(self.bytes(input_id))

    def toml(self, input_id: str) -> dict[str, Any]:
        return tomllib.loads(self.bytes(input_id).decode("utf-8"))

    def file(self, name: str) -> bytes:
        """A ``files/`` fixture referenced as ``{ corpus_file = "<name>" }``."""
        for input_id, entry in self.entries.items():
            if entry.get("path") == f"files/{name}":
                return self.bytes(input_id)
        msg = f"files/{name} is not in MANIFEST.toml"
        raise KeyError(msg)

    def fixture(self, input_id: str) -> dict[str, str | None]:
        return {"id": input_id, "sha256": self.entries[input_id].get("sha256")}


# ---------------------------------------------------------------------------------------------
# Case registry
# ---------------------------------------------------------------------------------------------

# A case setup gets a Ctx and returns the body to time: a sync callable or an async function.
Setup = Callable[["Ctx"], Callable[[], Any]]


@dataclass
class Case:
    id: str
    setup: Setup
    uses: tuple[str, ...] = ()
    variants: dict[str, list[str]] = field(default_factory=dict)
    kind: str = "time"  # time | rss (fresh-subprocess RSS per retained object) | sustained
    memory: bool = False  # also measure tracemalloc peak / retained of one call
    n: int = 0  # rss: retained objects per subprocess

    def expand(self) -> list[dict[str, str]]:
        combos: list[dict[str, str]] = [{}]
        for key, values in self.variants.items():
            combos = [{**c, key: v} for c in combos for v in values]
        return combos


class Registry(dict[str, Case]):
    def case(
        self,
        case_id: str,
        *,
        uses: Iterable[str] = (),
        variants: dict[str, list[str]] | None = None,
        kind: str = "time",
        memory: bool = False,
        n: int = 0,
    ) -> Callable[[Setup], Setup]:
        def register(setup: Setup) -> Setup:
            if case_id in self:
                msg = f"duplicate case {case_id}"
                raise ValueError(msg)
            self[case_id] = Case(case_id, setup, tuple(uses), variants or {}, kind, memory, n)
            return setup

        return register


REGISTRY = Registry()


def variant_label(case_id: str, variant: dict[str, str]) -> str:
    if not variant:
        return case_id
    return f"{case_id}[{','.join(f'{k}={v}' for k, v in variant.items())}]"


class Ctx:
    """What a case setup sees: the corpus (recording every fixture read), the adapter, the loop."""

    def __init__(self, corpus: Corpus, adapter: Any, loop: Any, variant: dict[str, str]) -> None:
        self.corpus = corpus
        self.adapter = adapter
        self.loop = loop
        self.variant = variant
        self.fixtures: dict[str, dict[str, str | None]] = {}
        self.cleanups: list[Callable[[], Any]] = []

    def _use(self, input_id: str) -> None:
        self.fixtures[input_id] = self.corpus.fixture(input_id)

    def bytes(self, input_id: str) -> bytes:
        self._use(input_id)
        return self.corpus.bytes(input_id)

    def json(self, input_id: str) -> Any:
        self._use(input_id)
        return self.corpus.json(input_id)

    def toml(self, input_id: str) -> dict[str, Any]:
        self._use(input_id)
        return self.corpus.toml(input_id)

    def entry(self, input_id: str) -> dict[str, Any]:
        self._use(input_id)
        return self.corpus.entry(input_id)

    def file(self, name: str) -> bytes:
        for input_id, entry in self.corpus.entries.items():
            if entry.get("path") == f"files/{name}":
                self._use(input_id)
        return self.corpus.file(name)

    def run(self, awaitable: Any) -> Any:
        return self.loop.run_until_complete(awaitable)

    def on_close(self, fn: Callable[[], Any]) -> None:
        self.cleanups.append(fn)


# ---------------------------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------------------------


def make_timer(body: Callable[[], Any], loop: Any) -> Callable[[int], float]:
    """Return ``timer(loops) -> seconds`` for a sync callable or an async function."""
    if inspect.iscoroutinefunction(body):

        async def many(loops: int) -> float:
            start = time.perf_counter()
            for _ in range(loops):
                await body()
            return time.perf_counter() - start

        return lambda loops: loop.run_until_complete(many(loops))

    def timer(loops: int) -> float:
        start = time.perf_counter()
        for _ in range(loops):
            body()
        return time.perf_counter() - start

    return timer


def gc_off(fn: Callable[[], float]) -> float:
    gc.collect()
    enabled = gc.isenabled()
    gc.disable()
    try:
        return fn()
    finally:
        if enabled:
            gc.enable()


def calibrate(timer: Callable[[int], float], min_sample_s: float) -> int:
    loops = 1
    while True:
        elapsed = gc_off(functools.partial(timer, loops))
        if elapsed >= min_sample_s:
            return loops
        # aim 10% past the target so the next try usually lands
        loops = max(loops * 2, int(loops * min_sample_s * 1.1 / max(elapsed, 1e-9)))


# ---------------------------------------------------------------------------------------------
# Statistics (stdlib only)
# ---------------------------------------------------------------------------------------------


def summarize(samples: list[float]) -> dict[str, float]:
    quartiles = statistics.quantiles(samples, n=4, method="inclusive")
    ventiles = statistics.quantiles(samples, n=20, method="inclusive")
    return {
        "median": statistics.median(samples),
        "iqr": quartiles[2] - quartiles[0],
        "p5": ventiles[0],
        "p95": ventiles[-1],
        "min": min(samples),
        "max": max(samples),
    }


def bootstrap_ci(
    base: list[float], head: list[float], resamples: int = 10_000, seed: int = 0
) -> tuple[float, float]:
    """95% percentile-bootstrap CI of median(head) / median(base) - 1."""
    rng = random.Random(seed)
    n, m = len(base), len(head)
    ratios = sorted(
        statistics.median(rng.choices(head, k=m)) / statistics.median(rng.choices(base, k=n)) - 1
        for _ in range(resamples)
    )
    return ratios[int(0.025 * resamples)], ratios[int(0.975 * resamples) - 1]


def mann_whitney_p(base: list[float], head: list[float]) -> float:
    """Two-sided exact Mann-Whitney U p-value.

    ponytail: exact null distribution assumes no ties (float timings); ties count as 0.5 and are
    rounded down, which only makes the test slightly conservative.
    """
    n, m = len(base), len(head)
    u = int(sum(1.0 if h > b else 0.5 if h == b else 0.0 for b in base for h in head))
    # counts[k][j][u]: arrangements of k base and j head values with statistic u
    counts = [[[0] * (n * m + 1) for _ in range(m + 1)] for _ in range(n + 1)]
    for k in range(n + 1):
        counts[k][0][0] = 1
    for j in range(m + 1):
        counts[0][j][0] = 1
    for k in range(1, n + 1):
        for j in range(1, m + 1):
            for s in range(n * m + 1):
                # the largest value is a head value (beats all k base values) or a base value
                counts[k][j][s] = (counts[k][j - 1][s - k] if s >= k else 0) + counts[k - 1][j][s]
    dist = counts[n][m]
    total = sum(dist)
    low = sum(dist[: u + 1]) / total
    high = sum(dist[u:]) / total
    return min(1.0, 2 * min(low, high))


def compare_samples(base: list[float], head: list[float]) -> dict[str, Any]:
    lo, hi = bootstrap_ci(base, head)
    return {
        "delta_median": statistics.median(head) / statistics.median(base) - 1,
        "ci95": [lo, hi],
        "mwu_p": mann_whitney_p(base, head),
    }


# ---------------------------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------------------------


def _cmd(*args: str, cwd: Path | None = None) -> str | None:
    try:
        out = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip()


def _read(path: str) -> str | None:
    try:
        return Path(path).read_text("utf-8").strip()
    except OSError:
        return None


def _cpu() -> dict[str, Any]:
    model = physical = None
    if sys.platform == "darwin":
        model = _cmd("sysctl", "-n", "machdep.cpu.brand_string")
        cores = _cmd("sysctl", "-n", "hw.physicalcpu")
        physical = int(cores) if cores and cores.isdigit() else None
    elif cpuinfo := _read("/proc/cpuinfo"):
        cores_seen = set()
        physical_id = core_id = None
        for line in cpuinfo.splitlines():
            key, _, value = (part.strip() for part in line.partition(":"))
            if key == "model name" and model is None:
                model = value
            elif key == "physical id":
                physical_id = value
            elif key == "core id":
                core_id = value
                cores_seen.add((physical_id, core_id))
        physical = len(cores_seen) or None
    return {
        "model": model or platform.processor() or None,
        "logical_cores": os.cpu_count(),
        "physical_cores": physical,
        "governor": _read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"),
    }


def _version(module: str) -> str | None:
    try:
        mod = __import__(module)
    except ImportError:
        return None
    return str(getattr(mod, "__version__", None) or getattr(mod, "VERSION", None))


def process_env(loop_name: str, corpus: Corpus) -> dict[str, Any]:
    """Everything the measuring process knows about itself (run inside the side's interpreter)."""
    is_gil_enabled = getattr(sys, "_is_gil_enabled", None)
    return {
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "build": list(platform.python_build()),
            "compiler": platform.python_compiler(),
            "executable": sys.executable,
            "free_threaded": bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
            "gil_enabled": is_gil_enabled() if is_gil_enabled else True,
        },
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "cpu": _cpu(),
        "loop": {
            "name": loop_name,
            "uvloop": _version("uvloop") if loop_name == "uvloop" else None,
        },
        "packages": {name: _version(name) for name in ("aiogram", "pydantic", "aiohttp")},
        "corpus": {"manifest_sha256": corpus.manifest_sha256},
        "extra": {},  # B-02: Cargo.lock / rustc / pyo3 / maturin / build flags
    }


def tree_env(tree: Path, commit: str | None = None) -> dict[str, Any]:
    """Git and lock state of a source tree; ``commit`` given for an exported (archived) tree."""
    lock = tree / "uv.lock"
    if commit is None:
        commit = _cmd("git", "rev-parse", "HEAD", cwd=tree)
        dirty = bool(_cmd("git", "status", "--porcelain", "--untracked-files=no", cwd=tree))
    else:
        dirty = False
    return {
        "git": {"commit": commit, "dirty": dirty},
        "uv_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest() if lock.exists() else None,
    }


def new_document(kind: str, settings: Settings, env: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "kind": kind,
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "argv": sys.argv,
        "settings": asdict(settings),
        "env": env,
        "results": [],
    }


def load_document(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text("utf-8"))
    if doc.get("schema") != SCHEMA:
        msg = f"{path}: unsupported schema {doc.get('schema')!r} (this harness reads {SCHEMA})"
        raise ValueError(msg)
    return doc
