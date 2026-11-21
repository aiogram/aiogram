"""Differential runner: side venvs, side execution, manifest loading, comparison and report.

See ``differential/README.md`` for the concepts. The CLI is ``python -m differential run``.
"""

from __future__ import annotations

import argparse
import difflib
import fnmatch
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NoReturn

from differential import trace

Record = dict[str, Any]
Trace = tuple[dict[str, Any], list[Record]]

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parent
STATE = REPO / ".differential"
KINDS = ("smoke", "model", "request", "routing")
CLASSES = ("invariant", "approved", "new")
ADAPTERS = ("aiogram3", "aiogram4")
ENTRY_KEYS = {"match", "class", "decision", "assert", "gate", "when", "note"}

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_POISON_NOT_DETECTED = 2
EXIT_HARNESS_ERROR = 3


class HarnessError(Exception):
    """The harness itself failed (bad spec, venv, side crash, bad manifest): exit 3."""


class Mismatch(Exception):  # noqa: N818 - it is an outcome, not an error
    """Raised by a comparator when its narrow assertion does not hold."""


# ------------------------------------------------------------------------------------------------
# Comparators
# ------------------------------------------------------------------------------------------------

Comparator = Callable[[Record, Record], tuple[Record, Record]]
COMPARATORS: dict[str, Comparator] = {}


def comparator(name: str) -> Callable[[Comparator], Comparator]:
    """Register a named comparator for ``approved`` entries.

    It gets the two records and returns them with its approved difference neutralised, or
    raises :class:`Mismatch` when the difference is not the approved one. The runner then
    requires the rest of the two records to be equal.
    """

    def register(func: Comparator) -> Comparator:
        if name in COMPARATORS:
            msg = f"comparator {name!r} registered twice"
            raise ValueError(msg)
        COMPARATORS[name] = func
        return func

    return register


def _stub(name: str, owner: str) -> None:
    """A seeded comparator its owning plan has not written yet: it never approves anything."""

    def compare(left: Record, right: Record) -> tuple[Record, Record]:
        msg = f"stub comparator {name!r}: refine in {owner}"
        raise Mismatch(msg)

    comparator(name)(compare)


# Seeded approved differences (manifests/*.toml). Each owning plan replaces its stub with the real
# narrow assertion and refines the entry's ``match``.
for _name, _owner in (
    ("equality_ignores_bot", "A-08 / B plans"),
    ("wire_names_in_dump_json", "A-08 / B plans"),
    ("json_shaped_extras", "A-08 / B plans"),
    ("dump_json_equals_to_json", "A-08 / B plans"),
    ("collections_are_tuples", "A-08 / B plans"),
    ("malformed_member_is_unknown", "A-08 / B plans"),
    ("as_returns_new_view", "A-08 / B plans"),
    ("json_body_without_files", "A-09 / D-15"),
):
    _stub(_name, _owner)


# Routing (A-10). The records are those of ``sides/aiogram3/routing.py``: ``trace``, ``kwargs`` and
# ``threads`` hold one entry per component call ({component, kind, router, path, update, ...});
# ``result`` one outcome per update. One record matches one manifest entry, so every routing
# comparator first applies the two 4.0 differences that hold everywhere: D12 on ``kwargs`` and D34
# on ``threads``.

D12_KEYS = ("event_from_user", "event_chat", "event_thread_id")


def _entries(record: Record) -> list[dict[str, Any]] | None:
    value = record.get("value")
    if record.get("ok") is not True or record.get("probe") not in {"trace", "kwargs", "threads"}:
        return None
    if not isinstance(value, list):
        msg = f"{record.get('probe')} value is not a list"
        raise Mismatch(msg)
    return value


def _with(record: Record, entries: list[dict[str, Any]]) -> Record:
    return {**record, "value": entries}


def _global_4x(left: Record, right: Record) -> tuple[Record, Record]:
    """D12 on ``kwargs`` and D34 on ``threads``; other records unchanged."""
    if (entries := _entries(left)) is None:
        return left, right
    if left["probe"] == "kwargs":
        for entry in _entries(right) or []:
            if found := [key for key in D12_KEYS if key in entry.get("data", {})]:
                msg = f"right still injects {found} at {entry.get('component')}"
                raise Mismatch(msg)
        entries = [
            {**e, "data": {k: v for k, v in e["data"].items() if k not in D12_KEYS}}
            for e in entries
        ]
    elif left["probe"] == "threads":
        entries = [{**e, "on_loop": True} if e["kind"] == "filter" else e for e in entries]
    return _with(left, entries), right


def _drop_groups(
    left: Record, right: Record, group: Callable[[dict[str, Any]], str | None]
) -> tuple[Record, Record]:
    """Right may lack whole groups of left's entries; nothing else.

    ``group`` names the droppable group of an entry (``None``: not droppable). A group that has
    any entry on the right is kept whole on the left, so a partial drop still mismatches.
    """
    left_entries, right_entries = _entries(left), _entries(right)
    if left_entries is None or right_entries is None:
        return left, right
    kept = {group(entry) for entry in right_entries} - {None}
    return _with(left, [e for e in left_entries if group(e) is None or group(e) in kept]), right


def _ran(entries: list[dict[str, Any]], kind: str = "handler") -> list[dict[str, Any]]:
    return [entry for entry in entries if entry["kind"] == kind]


@comparator("sync_filters_inline")
def sync_filters_inline(left: Record, right: Record) -> tuple[Record, Record]:
    """D34: sync filters run on the loop (``threads`` only); sync handlers stay in a thread."""
    return _global_4x(left, right)


@comparator("outer_middleware_skipped_without_handler")
def outer_middleware_skipped_without_handler(left: Record, right: Record) -> tuple[Record, Record]:
    """D111 / PD-19: right may skip a router (its outer middlewares and everything under them)
    whose subtree called no handler on the left."""
    left, right = _global_4x(left, right)
    entries = _entries(left) or []
    called = {(e["update"], r) for e in _ran(entries) for r in e["path"]}

    def group(entry: dict[str, Any]) -> str | None:
        for router in entry["path"]:  # outermost skippable router first
            if (entry["update"], router) not in called:
                return f"{entry['update']}/{router}"
        return None

    return _drop_groups(left, right, group)


@comparator("compiled_rejector_skips_handler")
def compiled_rejector_skips_handler(left: Record, right: Record) -> tuple[Record, Record]:
    """Breaking change 13: right may skip all user filters of a candidate whose handler the left
    did not call (a compiled rejector rejected it first)."""
    left, right = _global_4x(left, right)
    entries = _entries(left) or []
    called = {(e["update"], e["component"]) for e in _ran(entries)}

    def group(entry: dict[str, Any]) -> str | None:
        owner = entry.get("owner")
        if entry["kind"] != "filter" or owner is None or (entry["update"], owner) in called:
            return None
        return f"{entry['update']}/{owner}"

    return _drop_groups(left, right, group)


@comparator("errors_bubble_to_raising_router")
def errors_bubble_to_raising_router(left: Record, right: Record) -> tuple[Record, Record]:
    """D48: the ``errors`` handlers called are those on the raising router's path, innermost
    first, up to the first that handles it; everything else is equal."""
    left, right = _global_4x(left, right)
    if left.get("probe") == "result":
        return _error_result(left, right)
    entries, right_entries = _entries(left), _entries(right)
    if entries is None or right_entries is None:
        return left, right
    errors = _ran(entries, "error")
    if not errors:
        return left, right
    if left["probe"] == "trace":
        raising = next(
            (e for e in entries if isinstance(e["result"], dict) and "raised" in e["result"]), None
        )
        if raising is None:
            msg = "left has errors handlers but nothing raised"
            raise Mismatch(msg)
        by_router: dict[str, list[dict[str, Any]]] = {}
        for entry in errors:
            by_router.setdefault(entry["router"], []).append(entry)
        expected: list[dict[str, Any]] = []
        for router in reversed(raising["path"]):
            handled = False
            for entry in by_router.get(router, []):
                expected.append(entry)
                if entry["result"] != "UNHANDLED":
                    handled = True
                    break
            if handled:
                break
    else:  # kwargs: the same handlers as right's, in left's data
        wanted = [(e["component"], e["update"]) for e in _ran(right_entries, "error")]
        index = {(e["component"], e["update"]): e for e in errors}
        if any(key not in index for key in wanted):
            msg = "right calls an errors handler the left did not reach"
            raise Mismatch(msg)
        expected = [index[key] for key in wanted]
    first = entries.index(errors[0])
    rest = [e for e in entries if e["kind"] != "error"]
    return _with(left, [*rest[:first], *expected, *rest[first:]]), right


def _error_result(left: Record, right: Record) -> tuple[Record, Record]:
    """D48 on ``result``: an update the left's sibling handled may escape on the right."""
    lefts, rights = left.get("value"), right.get("value")
    if not isinstance(lefts, list) or not isinstance(rights, list) or len(lefts) != len(rights):
        return left, right
    merged = [
        r if l_out != r and isinstance(r, dict) and "raised" in r else l_out
        for l_out, r in zip(lefts, rights, strict=True)
    ]
    return {**left, "value": merged}, right


@comparator("event_isolation_default")
def event_isolation_default(left: Record, right: Record) -> tuple[Record, Record]:
    """D28 / D110: updates of one key are serialised: right is left stably sorted by update."""
    left, right = _global_4x(left, right)
    if (entries := _entries(left)) is None:
        return left, right
    return _with(left, sorted(entries, key=lambda entry: entry["update"])), right


@comparator("routing_snapshot_per_runner")
def routing_snapshot_per_runner(left: Record, right: Record) -> tuple[Record, Record]:
    """D114: a component registered while handling applies from the next update: right lacks
    the entries of registrations made in the same case; a later case is equal."""
    left, right = _global_4x(left, right)
    if left.get("probe") == "result":
        lefts, rights = left.get("value"), right.get("value")
        if isinstance(lefts, list) and rights == [{"returned": "UNHANDLED"}] * len(lefts):
            return {**left, "value": rights}, right  # the late router was the only match
        return left, right
    if (entries := _entries(left)) is None:
        return left, right
    here = {e["registers"] for e in entries if "registers" in e}
    return _with(left, [e for e in entries if e.get("late") not in here]), right


@comparator("event_context_only_kwargs")
def event_context_only_kwargs(left: Record, right: Record) -> tuple[Record, Record]:
    """D12: no ``event_from_user`` / ``event_chat`` / ``event_thread_id`` in the data. A handler
    asking for one by signature may fail with a DI error or run without it (E-21 narrows this)."""
    left, right = _global_4x(left, right)
    if left.get("probe") == "result":
        rights = right.get("value")
        if isinstance(rights, list) and all(isinstance(r, dict) and "raised" in r for r in rights):
            return {**left, "value": rights}, right
        return left, right
    entries, right_entries = _entries(left), _entries(right)
    if entries is None or right_entries is None:
        return left, right
    asked = {e["component"] for e in _ran(entries) if e.get("data") == {}}
    if left["probe"] == "kwargs":  # data was only the stripped key
        present = {e["component"] for e in _ran(right_entries)}
        entries = [e for e in entries if e["component"] not in asked - present]
    elif left["probe"] in {"trace", "threads"}:
        present = {e["component"] for e in _ran(right_entries)}
        entries = [e for e in entries if e["kind"] != "handler" or e["component"] in present]
    return _with(left, entries), right


# ------------------------------------------------------------------------------------------------
# Manifest
# ------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Entry:
    match: str
    cls: str
    decision: str | None = None
    assert_: str | None = None
    gate: bool = False
    when: str | None = None
    note: str | None = None


INVARIANT = Entry(match="*", cls="invariant")


def load_manifest(path: str | Path) -> list[Entry]:  # noqa: C901 - one check per schema rule
    path = Path(path)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        msg = f"{path}: {exc}"
        raise HarnessError(msg) from exc
    if set(data) - {"case"}:
        msg = f"{path}: unknown top-level keys {sorted(set(data) - {'case'})}"
        raise HarnessError(msg)
    entries = []
    for number, raw in enumerate(data.get("case", []), 1):
        where = f"{path}: case #{number}"
        if unknown := set(raw) - ENTRY_KEYS:
            msg = f"{where}: unknown keys {sorted(unknown)}"
            raise HarnessError(msg)
        if not isinstance(raw.get("match"), str) or not raw["match"]:
            msg = f"{where}: 'match' must be a non-empty string"
            raise HarnessError(msg)
        cls = raw.get("class")
        if cls not in CLASSES:
            msg = f"{where}: 'class' must be one of {CLASSES}, got {cls!r}"
            raise HarnessError(msg)
        if cls != "invariant" and not raw.get("decision"):
            msg = f"{where}: class {cls!r} needs a 'decision'"
            raise HarnessError(msg)
        if cls == "approved":
            if not isinstance(raw.get("assert"), str) or raw["assert"] not in COMPARATORS:
                got = raw.get("assert")
                msg = f"{where}: 'assert' must name a registered comparator, got {got!r}"
                raise HarnessError(msg)
        elif "assert" in raw:
            msg = f"{where}: 'assert' is only valid for class 'approved'"
            raise HarnessError(msg)
        if not isinstance(raw.get("gate", False), bool):
            msg = f"{where}: 'gate' must be a boolean"
            raise HarnessError(msg)
        if raw.get("when") is not None and raw["when"] not in ADAPTERS:
            msg = f"{where}: 'when' must be one of {ADAPTERS}"
            raise HarnessError(msg)
        entries.append(
            Entry(
                match=raw["match"],
                cls=cls,
                decision=raw.get("decision"),
                assert_=raw.get("assert"),
                gate=raw.get("gate", False),
                when=raw.get("when"),
                note=raw.get("note"),
            )
        )
    return entries


def classify(key: str, entries: list[Entry], adapters: set[str]) -> Entry:
    """First active entry whose glob matches ``<case>/<probe>``; unmatched keys are invariant."""
    for entry in entries:
        if entry.when is not None and entry.when not in adapters:
            continue
        if fnmatch.fnmatchcase(key, entry.match):
            return entry
    return INVARIANT


# ------------------------------------------------------------------------------------------------
# Comparison and report
# ------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Outcome:
    key: str
    entry: Entry
    reason: str | None  # None = matched
    left: Record | None
    right: Record | None


@dataclass
class Result:
    outcomes: list[Outcome] = field(default_factory=list)

    @property
    def mismatches(self) -> list[Outcome]:
        return [outcome for outcome in self.outcomes if outcome.reason is not None]


def _core(record: Record) -> str:
    """What invariant equality compares: ``meta`` (timings, platform) is left to comparators."""
    return trace.dumps({key: record.get(key) for key in ("ok", "value", "error")})


def _index(records: list[Record], side: str) -> dict[str, Record]:
    index: dict[str, Record] = {}
    for record in records:
        key = f"{record['case']}/{record['probe']}"
        if key in index:
            msg = f"{side} trace has {key} twice"
            raise HarnessError(msg)
        index[key] = record
    return index


def _judge(entry: Entry, left: Record, right: Record) -> str | None:
    if entry.cls == "new":
        if left.get("ok") is False and right.get("ok") is True:
            return None
        return f"new ({entry.decision}): expected left to fail and right to succeed"
    if entry.cls == "approved":
        assert entry.assert_ is not None  # noqa: S101 - guaranteed by load_manifest
        try:
            left, right = COMPARATORS[entry.assert_](left, right)
        except Mismatch as exc:
            return f"approved ({entry.decision}, {entry.assert_}): {exc}"
        if _core(left) != _core(right):
            return f"approved ({entry.decision}, {entry.assert_}): the rest of the record differs"
        return None
    if _core(left) != _core(right):
        return "invariant: records differ"
    return None


def compare(
    left: list[Record], right: list[Record], entries: list[Entry], adapters: set[str]
) -> Result:
    lefts, rights = _index(left, "left"), _index(right, "right")
    result = Result()
    for key in [*lefts, *(key for key in rights if key not in lefts)]:
        entry = classify(key, entries, adapters)
        l_rec, r_rec = lefts.get(key), rights.get(key)
        reason: str | None
        if l_rec is None or r_rec is None:
            reason = f"missing on {'left' if l_rec is None else 'right'}"
        else:
            reason = _judge(entry, l_rec, r_rec)
        result.outcomes.append(Outcome(key, entry, reason, l_rec, r_rec))
    return result


def _pretty(record: Record | None) -> list[str]:
    if record is None:
        return []
    return json.dumps(record, sort_keys=True, indent=1, ensure_ascii=False).splitlines()


def render(
    left_header: dict[str, Any], right_header: dict[str, Any], result: Result, max_diffs: int
) -> str:
    out = [f"left:  {trace.dumps(left_header)}", f"right: {trace.dumps(right_header)}", ""]
    out.append(f"{'class':<10} {'matched':>8} {'mismatched':>11}")
    for cls in CLASSES:
        rows = [outcome for outcome in result.outcomes if outcome.entry.cls == cls]
        bad = sum(outcome.reason is not None for outcome in rows)
        out.append(f"{cls:<10} {len(rows) - bad:>8} {bad:>11}")
    mismatches = result.mismatches
    for outcome in mismatches[:max_diffs]:
        out.extend(["", f"MISMATCH {outcome.key}: {outcome.reason}"])
        out.extend(
            difflib.unified_diff(
                _pretty(outcome.left), _pretty(outcome.right), "left", "right", lineterm="", n=2
            )
        )
    if len(mismatches) > max_diffs:
        out.append(f"\n... {len(mismatches) - max_diffs} more mismatches")
    return "\n".join(out)


def evaluate(
    left: Trace, right: Trace, entries: list[Entry], *, poison: str | None, max_diffs: int = 20
) -> tuple[int, str]:
    """Compare two traces; return ``(exit code, report)``.

    The CLI and the self-tests share this path.
    """
    adapters = {header["adapter"] for header, _ in (left, right) if "adapter" in header}
    result = compare(left[1], right[1], entries, adapters)
    report = render(left[0], right[0], result, max_diffs)
    if poison is not None and not result.mismatches:
        return EXIT_POISON_NOT_DETECTED, f"{report}\n\npoison not detected (--poison {poison})"
    if result.mismatches:
        return EXIT_MISMATCH, f"{report}\n\n{len(result.mismatches)} unapproved mismatch(es)"
    return EXIT_OK, f"{report}\n\n0 mismatches"


# ------------------------------------------------------------------------------------------------
# Sides
# ------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Side:
    spec: str
    scheme: str  # pypi | git | path
    target: str


def parse_side(spec: str) -> Side:
    scheme, sep, target = spec.partition(":")
    if not sep or not target or scheme not in {"pypi", "git", "path"}:
        msg = f"bad side {spec!r}: expected pypi:<requirement>, git:<ref> or path:<dir>"
        raise HarnessError(msg)
    return Side(spec, scheme, target)


def _run(cmd: list[str], *, cwd: Path | None = None, input_: bytes | None = None) -> bytes:
    env = {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}
    proc = subprocess.run(cmd, cwd=cwd, input=input_, capture_output=True, env=env, check=False)  # noqa: S603
    if proc.returncode != 0:
        tail = proc.stderr.decode(errors="replace")[-2000:]
        msg = f"command failed ({proc.returncode}): {' '.join(cmd)}\n{tail}"
        raise HarnessError(msg)
    return proc.stdout


def _uv() -> str:
    uv = os.environ.get("UV") or shutil.which("uv")
    if not uv:
        msg = "uv not found on PATH"
        raise HarnessError(msg)
    return uv


def _venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def prepare(side: Side) -> tuple[Path, str | None]:
    """Build (or reuse) the side's venv; return its python and the commit it was built from."""
    commit: str | None = None
    if side.scheme == "pypi":
        target, resolved = side.target, side.target
    elif side.scheme == "git":
        commit = (
            _run(["git", "rev-parse", "--verify", f"{side.target}^{{commit}}"], cwd=REPO)
            .decode()
            .strip()
        )
        src = STATE / "src" / commit
        if not (src / ".complete").exists():
            # `git archive`, not the plan's `git worktree`: no worktree bookkeeping
            shutil.rmtree(src, ignore_errors=True)
            src.mkdir(parents=True)
            archive = _run(["git", "archive", "--format=tar", commit], cwd=REPO)
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                if hasattr(tarfile, "data_filter"):  # 3.11.4+
                    tar.extractall(src, filter="data")
                else:  # our own `git archive` output
                    tar.extractall(src)  # noqa: S202
            (src / ".complete").touch()
        target, resolved = str(src), commit
    else:
        path = Path(side.target).resolve()
        if not path.is_dir():
            msg = f"{side.spec}: not a directory"
            raise HarnessError(msg)
        target, resolved = str(path), str(path)

    key = hashlib.sha256(f"{side.scheme}:{resolved}:{sys.executable}".encode()).hexdigest()[:16]
    venv = STATE / "venvs" / key
    python = _venv_python(venv)
    marker = venv / ".differential-complete"
    install = [_uv(), "pip", "install", "--quiet", "--python", str(python), target]
    if side.scheme == "path":
        # the directory's content changes between runs, and uv caches local builds by
        # pyproject.toml only: always rebuild, even into a fresh venv
        install[3:3] = ["--reinstall-package", "aiogram"]
    if not marker.exists():
        shutil.rmtree(venv, ignore_errors=True)
        _run([_uv(), "venv", "--quiet", "--python", sys.executable, str(venv)])
        _run(install)
        marker.touch()
    elif side.scheme == "path":
        _run(install)
    return python, commit


def adapter_for(version: str) -> str:
    major = version.split(".", 1)[0]
    adapter = f"aiogram{major}"
    if adapter not in ADAPTERS:
        msg = f"no adapter for aiogram {version}"
        raise HarnessError(msg)
    return adapter


def run_side(side: Side, kind: str, corpus: Path, out: Path, *, poison: bool) -> Trace:
    python, commit = prepare(side)
    version = (
        _run([str(python), "-I", "-c", "import aiogram; print(aiogram.__version__)"])
        .decode()
        .strip()
    )
    adapter = adapter_for(version)
    script = PACKAGE / "sides" / adapter / f"{kind}.py"
    if not script.exists():
        msg = f"no {kind!r} probe for {adapter} ({script.relative_to(REPO)} does not exist)"
        raise HarnessError(msg)
    header = {
        "side": side.spec,
        "adapter": adapter,
        "commit": commit,
        "kind": kind,
        "poison": poison,
    }
    cmd = [
        str(python),
        "-I",  # keeps the repository and cwd off the side's sys.path
        str(script),
        "--corpus",
        str(corpus),
        "--out",
        str(out),
        "--trace-module",
        str(PACKAGE / "trace.py"),
        "--header",
        json.dumps(header),
    ]
    if poison:
        cmd.append("--poison")
    _run(cmd)
    try:
        return trace.read(out)
    except ValueError as exc:
        raise HarnessError(str(exc)) from exc


# ------------------------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------------------------


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        # argparse exits 2, which would read as "poison not detected"
        self.print_usage(sys.stderr)
        self.exit(EXIT_HARNESS_ERROR, f"{self.prog}: error: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="python -m differential")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run one kind on two sides and compare the traces")
    run.add_argument("--kind", required=True, choices=KINDS)
    run.add_argument("--left", required=True, help="pypi:<requirement> | git:<ref> | path:<dir>")
    run.add_argument("--right", required=True, help="pypi:<requirement> | git:<ref> | path:<dir>")
    run.add_argument(
        "--poison", choices=("left", "right"), help="corrupt that side; expect mismatches"
    )
    run.add_argument("--corpus", type=Path, default=REPO / "benchmarks" / "corpus")
    run.add_argument("--manifest", type=Path, help="default: differential/manifests/<kind>.toml")
    run.add_argument("--max-diffs", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        entries = load_manifest(args.manifest or PACKAGE / "manifests" / f"{args.kind}.toml")
        left, right = parse_side(args.left), parse_side(args.right)
        (STATE / "traces").mkdir(parents=True, exist_ok=True)
        out_dir = Path(tempfile.mkdtemp(prefix=f"{args.kind}-", dir=STATE / "traces"))
        traces = [
            run_side(
                side, args.kind, args.corpus, out_dir / f"{name}.jsonl", poison=args.poison == name
            )
            for name, side in (("left", left), ("right", right))
        ]
        code, report = evaluate(
            traces[0], traces[1], entries, poison=args.poison, max_diffs=args.max_diffs
        )
    except HarnessError as exc:
        sys.stderr.write(f"harness error: {exc}\n")
        return EXIT_HARNESS_ERROR
    except Exception:  # noqa: BLE001 - a crash must never exit 1, which reads as "mismatches"
        sys.stderr.write(f"harness error: unexpected exception\n{traceback.format_exc()}")
        return EXIT_HARNESS_ERROR
    sys.stdout.write(f"{report}\ntraces: {out_dir}\n")
    return code
