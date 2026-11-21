"""Self-test of the benchmark harness in benchmarks/ (A-05), on fake cases with tiny timings."""

import io
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
if not (ROOT / "benchmarks" / "harness.py").exists():
    pytest.skip("benchmarks/ is not part of this tree (sdist)", allow_module_level=True)

from benchmarks.harness import (  # noqa: E402
    SCHEMA,
    Registry,
    Settings,
    bootstrap_ci,
    load_document,
    mann_whitney_p,
)
from benchmarks.runner import LocalSide, ProcessSide, measure, report, run  # noqa: E402
from benchmarks.worker import Worker  # noqa: E402

FAST = Settings(warmup=2, min_sample_s=0.005)


def fake_registry(slow: bool = False) -> Registry:
    registry = Registry()

    @registry.case("fake.case")
    def setup(ctx):
        raw = ctx.bytes("update.text.small")

        def body():
            if slow:
                time.sleep(0.001)
            return len(raw)

        return body

    return registry


def side(registry: Registry | None = None) -> LocalSide:
    return LocalSide(Worker(registry=registry))


def test_run_document():
    doc = run("fake.case", FAST, side=side(fake_registry()))

    assert doc["schema"] == SCHEMA
    assert doc["kind"] == "run"
    (result,) = doc["results"]
    assert result["status"] == "ok"
    assert len(result["samples"]) == 7
    assert result["loops"] >= 1
    assert {"median", "iqr", "p5", "p95"} <= result.keys()
    assert result["fixtures"][0]["id"] == "update.text.small"
    assert len(result["fixtures"][0]["sha256"]) == 64

    env = doc["env"]
    assert {"commit", "dirty"} <= env["git"].keys()
    assert len(env["uv_lock_sha256"]) == 64
    assert {"version", "implementation", "build", "free_threaded"} <= env["python"].keys()
    assert {"system", "release", "machine"} <= env["os"].keys()
    assert {"model", "logical_cores", "physical_cores", "governor"} <= env["cpu"].keys()
    assert {"name", "uvloop"} <= env["loop"].keys()
    assert {"aiogram", "pydantic"} <= env["packages"].keys()
    assert len(env["corpus"]["manifest_sha256"]) == 64


def test_json_round_trip(tmp_path):
    doc = run("fake.case", FAST, side=side(fake_registry()))
    path = tmp_path / "result.json"
    path.write_text(json.dumps(doc), encoding="utf-8")

    assert load_document(path) == doc
    out = io.StringIO()
    report([doc, load_document(path)], out)
    assert "fake.case" in out.getvalue()


def test_unknown_schema_is_refused(tmp_path):
    path = tmp_path / "result.json"
    path.write_text(json.dumps({"schema": SCHEMA + 1}), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported schema"):
        load_document(path)


def test_compare_detects_slowed_head():
    sides = {"base": side(fake_registry()), "head": side(fake_registry(slow=True))}
    for s in sides.values():
        s.call("init", settings=asdict(FAST))

    results, comparison = measure(sides, [("fake.case", {})], FAST)

    assert [r["side"] for r in results] == ["base", "head"]
    (row,) = comparison
    assert row["delta_median"] > 0
    assert row["ci95"][0] > 0  # the interval excludes "no change"
    assert row["mwu_p"] < 0.01


def test_statistics():
    a = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6]
    b = [x + 10 for x in a]
    assert mann_whitney_p(a, b) == pytest.approx(2 / 3432)  # fully separated 7 vs 7
    assert mann_whitney_p(a, list(a)) == 1.0
    lo, hi = bootstrap_ci(a, list(a))
    assert lo <= 0 <= hi


def test_missing_case_is_reported():
    doc = run("update.unknown-tag", FAST, side=side(fake_registry()))
    assert doc["results"][0]["status"] == "missing"


def test_unknown_id_is_rejected():
    with pytest.raises(SystemExit, match="unknown case"):
        run("no.such.id", FAST, side=side(fake_registry()))


def test_real_cases_in_worker_process():
    """The real worker protocol and two real cases, so adapter drift fails here first."""
    worker = ProcessSide(sys.executable, ROOT)
    try:
        worker.call("init", settings=asdict(FAST))
        cases = worker.call("cases")
        assert "routing.52-handlers" in cases
        for case_id in ("update.text.small", "callback_data.filter.miss"):
            prep = worker.call("prepare", case=case_id, variant={})
            assert prep["status"] == "ok"
            assert worker.call("sample") > 0
            worker.call("finish")
    finally:
        worker.close()
