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
    ("collections_are_tuples", "B plans"),
    ("outer_middleware_skipped_without_handler", "A-10 / E plans"),
    ("compiled_rejector_skips_handler", "A-10 / E plans"),
    ("errors_bubble_to_raising_router", "A-10 / E plans"),
    ("sync_filters_inline", "A-10 / E plans"),
    ("event_isolation_default", "A-10 / E plans"),
    ("routing_snapshot_per_runner", "A-10 / E plans"),
    ("event_context_only_kwargs", "A-10 / E plans"),
    ("json_body_without_files", "A-09 / D-15"),
):
    _stub(_name, _owner)


# Model kind (A-08): records of sides/aiogram3/model.py, entries in manifests/model.toml.


def _expect(condition: bool, why: str) -> None:
    if not condition:
        raise Mismatch(why)


def _ok(record: Record) -> bool:
    return record.get("ok") is True


def _error_type(record: Record) -> str | None:
    return None if _ok(record) else record.get("error", {}).get("type")


@comparator("equality_ignores_bot")
def equality_ignores_bot(left: Record, right: Record) -> tuple[Record, Record]:
    """D108: equal data bound to different bots compares equal (3.x: unequal)."""
    _expect(_ok(left) and left["value"] is False, "left does not compare the two objects unequal")
    _expect(_ok(right) and right["value"] is True, "right does not compare the two objects equal")
    return left, left


@comparator("wire_names_in_dump_json")
def wire_names_in_dump_json(left: Record, right: Record) -> tuple[Record, Record]:
    """D86 / D94: ``model_dump_json()`` is the wire-name dump, still a ``str``.

    ``dump_json.default`` holds ``{type, value, wire}``: ``model_dump_json()`` and
    ``model_dump_json(by_alias=True, exclude_unset=True)``. Right's default dump must be left's
    wire dump.
    """
    _expect(_ok(left) and _ok(right), "dump_json failed on a side")
    wire = left["value"]["wire"]
    _expect(
        right["value"] == {"type": "str", "value": wire, "wire": wire},
        "right model_dump_json() is not left's wire-name dump as str",
    )
    return left, left


@comparator("json_shaped_extras")
def json_shaped_extras(left: Record, right: Record) -> tuple[Record, Record]:
    """D87: a non-JSON extra is a ``TypeError`` (3.x keeps any object)."""
    _expect(_ok(left), "left rejected the non-JSON extra")
    _expect(_error_type(right) == "TypeError", "right did not raise TypeError")
    return left, left


@comparator("hashable_when_fields_are")
def hashable_when_fields_are(left: Record, right: Record) -> tuple[Record, Record]:
    """D108 / D106: hashable when every field is (3.x: ``TypeError`` on list fields)."""
    _expect(_ok(right) and right["value"] == "int", "right is not hashable")
    _expect(
        (_ok(left) and left["value"] == "int") or _error_type(left) == "TypeError",
        "left neither hashes nor raises TypeError",
    )
    return right, right


@comparator("immutable_types")
def immutable_types(left: Record, right: Record) -> tuple[Record, Record]:
    """D15: attribute assignment raises on every type (3.x: MutableTelegramObject allows it)."""
    _expect(not _ok(right), "right allowed the assignment")
    return left, left


@comparator("replace_validates")
def replace_validates(left: Record, right: Record) -> tuple[Record, Record]:
    """R06: ``model_copy(update=...)`` is ``replace``, which validates (3.x stores the value)."""
    _expect(_ok(left) and left["value"].get("type") == "str", "left validated the update")
    _expect(not _ok(right), "right accepted an invalid value")
    return left, left


@comparator("as_returns_new_view")
def as_returns_new_view(left: Record, right: Record) -> tuple[Record, Record]:
    """D103: ``obj.as_(bot)`` returns a new bound view; the original keeps its bot."""
    _expect(
        _ok(left) and left["value"]["returns_self"] is True,
        "left as_() did not rebind in place",
    )
    view = {
        "returns_self": False,
        "original": "bot",
        "view": "other",
        "view_child": "other",
        "root": "bot",
    }
    _expect(_ok(right) and right["value"] == view, "right as_() is not a new view")
    return left, left


@comparator("nesting_limit_on_dict_path")
def nesting_limit_on_dict_path(left: Record, right: Record) -> tuple[Record, Record]:
    """3.33.0 (GHSA-hv98-r5fx-wc83): ``model_validate`` rejects a too-deep update.

    3.32.0 decoded it. The pydantic-core error type and locations depend on its version, which
    each venv resolves on its own, so only the recursion error kind is asserted.
    """
    recursion = {"recursion_loop", "recursion_depth_exceeded"}

    def rejected(record: Record) -> bool:
        if _error_type(record) != "ValidationError":
            return False
        errors = record["error"]["attrs"].get("errors", [])
        return bool(errors) and {item["type"] for item in errors} <= recursion

    _expect(rejected(right), "right did not reject the update with a recursion error")
    _expect(_ok(left) or rejected(left), "left failed with another error")
    return right, right


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
