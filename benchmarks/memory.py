"""Memory probes: tracemalloc for one call, RSS of the current process (R04)."""

from __future__ import annotations

import gc
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    import tracemalloc
except ImportError:  # PyPy has no tracemalloc: its fields stay null
    tracemalloc = None  # type: ignore[assignment]


def traced(call: Callable[[], Any]) -> dict[str, int | None]:
    """tracemalloc peak and retained bytes of one call, the result still held when read."""
    if tracemalloc is None:
        return {"peak": None, "retained": None}
    gc.collect()
    tracemalloc.start()
    try:
        before = tracemalloc.get_traced_memory()[0]
        result = call()
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    del result
    return {"peak": peak - before, "retained": current - before}


def rss() -> dict[str, Any]:
    """Current RSS (``/proc/self/statm``, Linux) and peak RSS (``ru_maxrss``), both in bytes."""
    current = peak = None
    try:
        statm = Path("/proc/self/statm").read_text("ascii")
    except OSError:
        pass
    else:
        current = int(statm.split()[1]) * os.sysconf("SC_PAGE_SIZE")
    try:
        import resource
    except ImportError:  # Windows: not a target, RSS fields stay null
        pass
    else:
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak *= 1 if sys.platform == "darwin" else 1024  # bytes on macOS, KiB elsewhere
    return {
        "current": current,
        "peak": peak,
        "source": "statm" if current is not None else "ru_maxrss" if peak is not None else None,
    }


def rss_value(reading: dict[str, Any]) -> int | None:
    """The figure to compare: current RSS where readable, peak RSS otherwise."""
    return reading["current"] if reading["current"] is not None else reading["peak"]
