"""Drives sides: ``run`` (one in-process side), ``compare`` (two worker processes), ``report``."""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any, Protocol, TextIO

from benchmarks.harness import (
    PACKAGE,
    Corpus,
    Settings,
    compare_samples,
    new_document,
    summarize,
    tree_env,
    variant_label,
)
from benchmarks.worker import Worker

REPO = PACKAGE.parent
STATE = REPO / ".benchmarks"  # cached exported trees and venvs, gitignored
WORKTREE = "WORKTREE"


class SideError(RuntimeError):
    pass


class Side(Protocol):
    def call(self, op: str, **args: Any) -> Any: ...
    def close(self) -> None: ...


class LocalSide:
    """A Worker in this process (``run``, and the self-test)."""

    def __init__(self, worker: Worker | None = None) -> None:
        self.worker = worker or Worker()

    def call(self, op: str, **args: Any) -> Any:
        return getattr(self.worker, f"op_{op}")(**args)

    def close(self) -> None:
        self.worker.op_close()


class ProcessSide:
    """A worker process under another interpreter, JSON lines over its stdin/stdout."""

    def __init__(self, python: str, harness: Path) -> None:
        self.proc = subprocess.Popen(
            [python, "-I", str(harness / "benchmarks" / "worker.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

    def call(self, op: str, **args: Any) -> Any:
        assert self.proc.stdin is not None and self.proc.stdout is not None
        self.proc.stdin.write(json.dumps({"op": op, "args": args}) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            msg = f"worker exited during {op!r} (code {self.proc.wait()})"
            raise SideError(msg)
        reply = json.loads(line)
        if "error" in reply:
            raise SideError(f"{op}: {reply['error']}")
        return reply["ok"]

    def close(self) -> None:
        if self.proc.stdin:
            self.proc.stdin.close()
        try:
            self.proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()


# ---------------------------------------------------------------------------------------------
# Measuring
# ---------------------------------------------------------------------------------------------


def select(available: dict[str, list[dict[str, str]]], spec: str, known: set[str]) -> list[Any]:
    """``--cases`` -> [(id, variant)]; ``all`` is every registered case."""
    ids = sorted(available) if spec == "all" else [s.strip() for s in spec.split(",") if s.strip()]
    unknown = [i for i in ids if i not in available and i not in known]
    if unknown:
        msg = f"unknown case id(s): {', '.join(unknown)}"
        raise SystemExit(msg)
    return [(i, v) for i in ids for v in available.get(i, [{}])]


def measure(
    sides: dict[str, Side], cases: list[Any], settings: Settings, log: TextIO | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Measure each case on every side, samples interleaved A/B/A/B; -> results, comparison."""
    results, comparison = [], []
    single = len(sides) == 1
    for case_id, variant in cases:
        label = variant_label(case_id, variant)
        if log:
            log.write(f"{label} ...\n")
            log.flush()
        preps = {
            name: side.call("prepare", case=case_id, variant=variant)
            for name, side in sides.items()
        }
        samples: dict[str, list[float]] = {name: [] for name in sides}
        extras: dict[str, dict[str, Any]] = {name: {} for name in sides}
        ready = {name for name, prep in preps.items() if prep["status"] == "ok"}
        if ready == set(sides):
            kind = next(iter(preps.values()))["kind"]
            if kind == "sustained":
                for name, side in sides.items():  # ponytail: sequential, not interleaved
                    out = side.call("sustained")
                    samples[name] = out["samples"]
                    extras[name]["sustained"] = out["sustained"]
            else:
                for _ in range(settings.repeats):
                    for name, side in sides.items():
                        samples[name].append(side.call("sample"))
        for name in ready:  # runs the case's cleanups, also on a side left unpaired
            extras[name].update(sides[name].call("finish"))
        for name, prep in preps.items():
            entry: dict[str, Any] = {"case": case_id, "variant": variant, "label": label}
            if not single:
                entry["side"] = name
            paired = ready == set(sides)
            # a side that could run while the other could not has nothing to be compared with
            entry["status"] = prep["status"] if paired or prep["status"] != "ok" else "unpaired"
            if paired:
                entry.update(
                    unit=prep["unit"],
                    kind=prep["kind"],
                    loops=prep["loops"],
                    fixtures=prep["fixtures"],
                    samples=samples[name],
                    **_summary(samples[name]),
                    **extras[name],
                )
            results.append(entry)
        if not single and ready == set(sides):
            base, head = samples.values()  # compare: exactly base and head
            if _finite(base) and _finite(head):
                comparison.append(
                    {
                        "case": case_id,
                        "variant": variant,
                        "label": label,
                        **compare_samples(base, head),
                    }
                )
    return results, comparison


def _finite(samples: list[float]) -> bool:
    return len(samples) > 1 and all(math.isfinite(s) for s in samples)


def _summary(samples: list[float]) -> dict[str, float]:
    return summarize(samples) if _finite(samples) else {}


# ---------------------------------------------------------------------------------------------
# Trees and venvs for compare
# ---------------------------------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.strip()


def export_tree(ref: str) -> tuple[str, Path]:
    """``git archive`` of ``ref`` into ``.benchmarks/trees/<sha>`` (no git worktree is created)."""
    sha = _git("rev-parse", "--verify", f"{ref}^{{commit}}")
    tree = STATE / "trees" / sha
    if not (tree / ".complete").exists():
        shutil.rmtree(tree, ignore_errors=True)
        tree.mkdir(parents=True)
        proc = subprocess.Popen(
            ["git", "archive", "--format=tar", sha], cwd=REPO, stdout=subprocess.PIPE
        )
        with tarfile.open(fileobj=proc.stdout, mode="r|") as archive:
            archive.extractall(tree, filter="data")
        if proc.wait():
            msg = f"git archive {sha} failed"
            raise SideError(msg)
        (tree / ".complete").touch()
    return sha, tree


def ensure_venv(sha: str, tree: Path) -> str:
    """``uv sync --locked`` of an exported tree into ``.benchmarks/venvs/<sha>-<python>``, cached.

    The venv is built on this interpreter, so both sides of a compare run the same Python.
    """
    python_tag = f"{sys.implementation.name}{'.'.join(map(str, sys.version_info[:3]))}"
    venv = STATE / "venvs" / f"{sha}-{python_tag}"
    marker = venv / ".benchmarks-complete"
    if not marker.exists():
        env = {k: v for k, v in os.environ.items() if k not in {"VIRTUAL_ENV", "UV_NO_SYNC"}}
        env["UV_PROJECT_ENVIRONMENT"] = str(venv)
        subprocess.run(
            ["uv", "sync", "--locked", "--no-dev", "--all-extras", "--quiet"]
            + ["--python", sys.executable],
            cwd=tree,
            env=env,
            check=True,
        )
        marker.touch()
    scripts = "Scripts" if sys.platform == "win32" else "bin"
    return str(venv / scripts / ("python.exe" if sys.platform == "win32" else "python"))


def resolve(ref: str) -> tuple[str, dict[str, Any]]:
    """A ``--base`` / ``--head`` value -> (interpreter, tree environment)."""
    if ref == WORKTREE:
        return sys.executable, {"ref": ref, **tree_env(REPO)}
    sha, tree = export_tree(ref)
    return ensure_venv(sha, tree), {"ref": ref, **tree_env(tree, commit=sha)}


def copy_harness(dest: Path) -> Path:
    """This checkout's ``benchmarks/`` (code + corpus) alone, so both sides run the same cases."""
    shutil.copytree(
        PACKAGE,
        dest / "benchmarks",
        ignore=shutil.ignore_patterns("__pycache__", "results", "record"),
    )
    return dest


# ---------------------------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------------------------


def run(
    spec: str, settings: Settings, log: TextIO | None = None, side: Side | None = None
) -> dict[str, Any]:
    side = side or LocalSide()
    try:
        env = side.call("init", settings=asdict(settings))
        env.update(tree_env(REPO))
        doc = new_document("run", settings, env)
        cases = select(side.call("cases"), spec, set(Corpus().entries))
        doc["results"], _ = measure({"run": side}, cases, settings, log)
    finally:
        side.close()
    return doc


def compare(
    base: str, head: str, spec: str, settings: Settings, log: TextIO | None = None
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="aiogram-bench-") as tmp:
        harness = copy_harness(Path(tmp))
        sides: dict[str, Side] = {}
        envs: dict[str, Any] = {}
        try:
            for name, ref in (("base", base), ("head", head)):
                python, env = resolve(ref)
                sides[name] = ProcessSide(python, harness)
                envs[name] = {**env, **sides[name].call("init", settings=asdict(settings))}
                # the first side resolves `auto`; the second must run the same loop or fail
                settings.loop = envs[name]["loop"]["name"]
            versions = {name: env["python"]["version"] for name, env in envs.items()}
            if len(set(versions.values())) > 1:
                msg = f"base and head run different Pythons: {versions}"
                raise SideError(msg)
            available = sides["head"].call("cases")
            cases = select(available, spec, set(Corpus().entries))
            doc = new_document("compare", settings, envs)
            doc["results"], doc["comparison"] = measure(sides, cases, settings, log)
        finally:
            for side in sides.values():
                try:
                    side.close()
                except Exception as e:  # noqa: BLE001  close the others, keep the first error
                    sys.stderr.write(f"closing a worker failed: {e}\n")
    return doc


def report(docs: list[dict[str, Any]], out: TextIO) -> None:
    """One run: its table. One compare, or two runs (``a`` = base, ``b`` = head): A/B rows.

    Cases that were not measured on both sides are listed with their status, never dropped.
    """
    if len(docs) == 1 and docs[0]["kind"] == "run":
        out.write(
            f"{'case':44} {'unit':>4} {'median':>12} {'iqr':>10} {'p5':>12} {'p95':>12}  status\n"
        )
        for r in docs[0]["results"]:
            if "median" in r:
                out.write(
                    f"{r['label']:44} {r['unit']:>4} {r['median']:12.3f} {r['iqr']:10.3f} "
                    f"{r['p5']:12.3f} {r['p95']:12.3f}  {r['status']}\n"
                )
            else:
                out.write(
                    f"{r['label']:44} {'':>4} {'':>12} {'':>10} {'':>12} {'':>12}  {r['status']}\n"
                )
        return
    if len(docs) == 1:
        doc = docs[0]
        base = {r["label"]: r for r in doc["results"] if r.get("side") == "base"}
        head = {r["label"]: r for r in doc["results"] if r.get("side") == "head"}
        stats = {c["label"]: c for c in doc.get("comparison", [])}
    else:
        base, head = (_by_label(d) for d in docs)
        stats = {
            label: compare_samples(ra["samples"], head[label]["samples"])
            for label, ra in base.items()
            if label in head and _comparable(ra, head[label])
        }
    labels = list(dict.fromkeys([*base, *head]))
    _table(out, [(label, base.get(label), head.get(label), stats.get(label)) for label in labels])


def _comparable(ra: dict[str, Any], rb: dict[str, Any]) -> bool:
    return (
        "median" in ra
        and "median" in rb
        and ra["unit"] == rb["unit"]
        and _finite(ra["samples"])
        and _finite(rb["samples"])
    )


def _by_label(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Results by label; a compare document contributes its head side."""
    return {
        r["label"]: r
        for r in doc["results"]
        if r.get("side", "head") == "head" or doc["kind"] == "run"
    }


def _table(out: TextIO, rows: list[Any]) -> None:
    out.write(
        f"{'case':44} {'unit':>4} {'base':>12} {'head':>12} {'ratio':>7} {'Δ median':>9} "
        f"{'95% CI (bootstrap)':>20} {'MWU p':>7}  {'head p5..p95':>22}\n"
    )
    for label, ra, rb, c in rows:
        if c is None:
            base_status = ra["status"] if ra else "absent"
            head_status = rb["status"] if rb else "absent"
            out.write(f"{label:44} base: {base_status}, head: {head_status}\n")
            continue
        if c["delta_median"] is None:  # base median <= 0: no ratio, absolute delta instead
            ratio, delta, ci = "n/a", f"{c['delta_abs']:+.1f}", "n/a"
        else:
            ratio = f"{rb['median'] / ra['median']:.3f}"
            delta = f"{c['delta_median']:+.1%}"
            ci = f"[{c['ci95'][0]:+.1%}, {c['ci95'][1]:+.1%}]" if c["ci95"] else "n/a"
        spread = f"{rb['p5']:.3f}..{rb['p95']:.3f}"
        out.write(
            f"{label:44} {rb['unit']:>4} {ra['median']:12.3f} {rb['median']:12.3f} "
            f"{ratio:>7} {delta:>9} {ci:>20} {c['mwu_p']:7.3f}  {spread:>22}\n"
        )
