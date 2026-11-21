"""Self-tests of the differential harness (``differential/``), with fake in-process sides: no venvs."""

import ast
import datetime
import decimal
import enum
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
if not (ROOT / "differential").is_dir():  # sdist: differential/ is not shipped
    pytest.skip("differential/ is not part of this checkout", allow_module_level=True)

from differential import runner, trace  # noqa: E402
from differential.runner import Entry, HarnessError, Mismatch  # noqa: E402

Record = dict[str, Any]


def fake_side(poison: bool = False) -> list[Record]:
    """A stand-in for a side script: decode two cases, optionally corrupt one field per object."""
    values = {"a": {"id": 1, "text": "x"}, "b": {"id": 2, "text": "y"}}
    records = []
    for case, value in values.items():
        if poison:
            value = {**value, "id": value["id"] + 1}
        records.append(trace.ok(case, "dump", value, meta={"elapsed": 0.1}))
    return records


def as_trace(records: list[Record], adapter: str = "aiogram3") -> runner.Trace:
    return {"side": "fake", "adapter": adapter}, records


def write_manifest(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "m.toml"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def registered():
    """Comparators registered by a test, removed afterwards."""
    added: list[str] = []

    def register(name: str, func: runner.Comparator) -> None:
        runner.comparator(name)(func)
        added.append(name)

    yield register
    for name in added:
        del runner.COMPARATORS[name]


class TestTrace:
    class Color(enum.Enum):
        RED = "red"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, None),
            (True, True),
            (1.5, 1.5),
            (float("nan"), {"__kind__": "float", "repr": "nan"}),
            (float("-inf"), {"__kind__": "float", "repr": "-inf"}),
            (b"\x00\xff", {"__kind__": "bytes", "b64": "AP8="}),
            ({3, 1, 2}, {"__kind__": "set", "items": [1, 2, 3]}),
            (frozenset({"b", "a"}), {"__kind__": "set", "items": ["a", "b"]}),
            ((1, [2]), {"__kind__": "tuple", "items": [1, [2]]}),
            (datetime.date(2026, 1, 2), {"__kind__": "date", "iso": "2026-01-02"}),
            (
                datetime.datetime(2026, 1, 2, 3, 4, tzinfo=datetime.UTC),
                {"__kind__": "datetime", "iso": "2026-01-02T03:04:00+00:00"},
            ),
            (datetime.time(1, 2), {"__kind__": "time", "iso": "01:02:00"}),
            (
                datetime.timedelta(days=1, seconds=2, microseconds=3),
                {"__kind__": "timedelta", "days": 1, "seconds": 2, "microseconds": 3},
            ),
            (decimal.Decimal("1.10"), {"__kind__": "decimal", "str": "1.10"}),
            ({1: "a"}, {"__kind__": "dict", "items": [[1, "a"]]}),
            ({"__kind__": "x"}, {"__kind__": "dict", "items": [["__kind__", "x"]]}),
            ({"k": (1,)}, {"k": {"__kind__": "tuple", "items": [1]}}),
        ],
    )
    def test_canonical(self, value, expected):
        assert trace.canonical(value) == expected
        trace.dumps(trace.canonical(value))  # always serialisable

    def test_canonical_enum_and_repr(self):
        assert trace.canonical(self.Color.RED) == {
            "__kind__": "enum",
            "type": f"{__name__}.TestTrace.Color",
            "value": "red",
        }
        tagged = trace.canonical(object())
        assert tagged["__kind__"] == "repr"
        assert tagged["type"] == "builtins.object"

    def test_dumps_is_canonical(self):
        assert trace.dumps({"b": 1, "a": "é"}) == '{"a":"é","b":1}'
        with pytest.raises(ValueError):
            trace.dumps(float("nan"))

    def test_error_record(self):
        record = trace.error("c", "p", ValueError("boom"))
        assert record == {
            "case": "c",
            "probe": "p",
            "ok": False,
            "error": {"type": "ValueError", "attrs": {"message": "boom"}},
            "meta": {},
        }
        assert trace.error("c", "p", ValueError(), attrs={"n": 1})["error"]["attrs"] == {"n": 1}

    def test_write_read_round_trip(self, tmp_path):
        path = tmp_path / "t.jsonl"
        records = fake_side()
        trace.write(path, {"side": "x"}, records)
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == '{"__header__":{"side":"x"}}'
        assert lines[1] == trace.dumps(records[0])
        assert trace.read(path) == ({"side": "x"}, records)

    @pytest.mark.parametrize("content", ["", '{"case": "a"}\n'])
    def test_read_rejects_missing_header(self, tmp_path, content):
        path = tmp_path / "t.jsonl"
        path.write_text(content, encoding="utf-8")
        with pytest.raises(ValueError):
            trace.read(path)

    def test_trace_module_is_stdlib_only(self):
        tree = ast.parse((ROOT / "differential" / "trace.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        assert imported <= sys.stdlib_module_names | {"__future__"}


class TestManifest:
    def test_glob_first_match_wins_and_default_invariant(self):
        entries = [
            Entry(match="model.update.*/dump", cls="new", decision="D10"),
            Entry(match="model.*", cls="approved", decision="D86", assert_="x"),
        ]
        assert runner.classify("model.update.a/dump", entries, set()).decision == "D10"
        assert runner.classify("model.update.a/decode", entries, set()).decision == "D86"
        assert runner.classify("request.x/y", entries, set()) is runner.INVARIANT

    def test_glob_is_case_sensitive(self):
        entries = [Entry(match="Model.*", cls="new", decision="D10")]
        assert runner.classify("model.a/b", entries, set()) is runner.INVARIANT

    def test_when_filters_by_adapter(self):
        entries = [Entry(match="*", cls="new", decision="D10", when="aiogram4")]
        assert runner.classify("a/b", entries, {"aiogram3"}) is runner.INVARIANT
        assert runner.classify("a/b", entries, {"aiogram3", "aiogram4"}).decision == "D10"

    def test_load(self, tmp_path):
        path = write_manifest(
            tmp_path,
            """
            [[case]]
            match = "a.*"
            class = "approved"
            decision = "D86"
            assert = "wire_names_in_dump_json"
            gate = true
            when = "aiogram4"
            note = "n"

            [[case]]
            match = "b.*"
            class = "invariant"
            """,
        )
        assert runner.load_manifest(path) == [
            Entry("a.*", "approved", "D86", "wire_names_in_dump_json", True, "aiogram4", "n"),
            Entry("b.*", "invariant"),
        ]

    def test_load_empty(self, tmp_path):
        assert runner.load_manifest(write_manifest(tmp_path, "# nothing\n")) == []

    @pytest.mark.parametrize(
        ("text", "error"),
        [
            ("schema = 1", "unknown top-level keys"),
            ('[[case]]\nmatch = "a"\nclass = "invariant"\nextra = 1', "unknown keys"),
            ('[[case]]\nclass = "invariant"', "'match' must be"),
            ('[[case]]\nmatch = ""\nclass = "invariant"', "'match' must be"),
            ('[[case]]\nmatch = "a"\nclass = "parity"', "'class' must be"),
            ('[[case]]\nmatch = "a"\nclass = "new"', "needs a 'decision'"),
            ('[[case]]\nmatch = "a"\nclass = "approved"\nassert = "x"', "needs a 'decision'"),
            (
                '[[case]]\nmatch = "a"\nclass = "approved"\ndecision = "D1"',
                "registered comparator",
            ),
            (
                '[[case]]\nmatch = "a"\nclass = "approved"\ndecision = "D1"\nassert = "nope"',
                "registered comparator",
            ),
            (
                '[[case]]\nmatch = "a"\nclass = "new"\ndecision = "D1"\nassert = "json_shaped_extras"',
                "only valid for class 'approved'",
            ),
            ('[[case]]\nmatch = "a"\nclass = "invariant"\ngate = "yes"', "'gate' must be"),
            ('[[case]]\nmatch = "a"\nclass = "invariant"\nwhen = "aiogram5"', "'when' must be"),
            ("[[case]\n", "m.toml"),
        ],
    )
    def test_load_rejects(self, tmp_path, text, error):
        with pytest.raises(HarnessError, match=error):
            runner.load_manifest(write_manifest(tmp_path, text))

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(HarnessError):
            runner.load_manifest(tmp_path / "absent.toml")

    @pytest.mark.parametrize("kind", runner.KINDS)
    def test_shipped_manifests_load(self, kind):
        runner.load_manifest(ROOT / "differential" / "manifests" / f"{kind}.toml")

    def test_seeded_entries(self):
        gated = {
            "D84",
            "D85",
            "D86",
            "D87",
            "D91",
            "D92",
            "D93",
            "D94",
            "D95",
            "D103",
            "D106",
            "D107",
            "D108",
        }
        gated.add("R06")  # A-08: model_copy -> replace, through D91
        three_x = {"GHSA-hv98-r5fx-wc83"}  # A-08: 3.32.0 vs later 3.x
        decisions = set()
        for kind in ("model", "request", "routing"):
            for entry in runner.load_manifest(
                ROOT / "differential" / "manifests" / f"{kind}.toml"
            ):
                decisions.add(entry.decision)
                assert entry.decision
                if entry.cls == "approved":
                    assert entry.assert_ in runner.COMPARATORS
                assert entry.gate is (entry.decision in gated)
                # 4.0 entries never apply to 3.x-vs-3.x runs
                assert entry.when == "aiogram4" or entry.decision in three_x
        expected = {
            "D108",
            "D86",
            "D87",
            "D94",
            "D106",
            "D107",
            "D10",
            "D103",
            "D111",
            "BC13",
            "D48",
        }
        expected |= {"D34", "D28", "D114", "D12", "R18"}
        expected = (expected - {"D94"}) | {"D15", "R06", *three_x}  # A-08
        assert decisions == expected

    def test_stub_comparators_never_approve(self):
        record = trace.ok("a", "b", 1)
        with pytest.raises(Mismatch, match="refine in"):
            runner.COMPARATORS["collections_are_tuples"](record, record)

    def test_comparator_registered_twice(self):
        with pytest.raises(ValueError, match="twice"):
            runner.comparator("wire_names_in_dump_json")(lambda left, right: (left, right))


class TestComparators:
    def judge(
        self, entries: list[Entry], left: list[Record], right: list[Record]
    ) -> runner.Result:
        return runner.compare(left, right, entries, {"aiogram3"})

    def test_invariant_equal(self):
        result = self.judge([], fake_side(), fake_side())
        assert [outcome.reason for outcome in result.outcomes] == [None, None]

    def test_invariant_ignores_meta(self):
        right = [{**record, "meta": {"elapsed": 9}} for record in fake_side()]
        assert not self.judge([], fake_side(), right).mismatches

    def test_invariant_bool_is_not_int(self):
        result = self.judge([], [trace.ok("a", "b", True)], [trace.ok("a", "b", 1)])
        assert result.mismatches[0].reason == "invariant: records differ"

    def test_invariant_differs(self):
        result = self.judge([], fake_side(), fake_side(poison=True))
        assert [outcome.key for outcome in result.mismatches] == ["a/dump", "b/dump"]

    def test_missing_on_either_side(self):
        left, right = fake_side(), fake_side()
        result = self.judge([], left[:1], right[1:])
        assert [(o.key, o.reason) for o in result.outcomes] == [
            ("a/dump", "missing on right"),
            ("b/dump", "missing on left"),
        ]

    def test_duplicate_key(self):
        with pytest.raises(HarnessError, match="twice"):
            self.judge([], fake_side() * 2, fake_side())

    def test_new(self):
        entries = [Entry(match="a/*", cls="new", decision="D10")]
        failed = [trace.error("a", "dump", ValueError("x"))]
        assert not self.judge(entries, failed, fake_side()[:1]).mismatches
        for left, right in ((fake_side(), fake_side()), (failed, failed), (fake_side(), failed)):
            reason = self.judge(entries, left[:1], right[:1]).mismatches[0].reason
            assert reason.startswith("new (D10)")

    @pytest.fixture
    def id_shift(self, registered):
        """Approved difference: right's ``id`` is left's + 1."""

        def compare(left: Record, right: Record) -> tuple[Record, Record]:
            if right["value"]["id"] != left["value"]["id"] + 1:
                raise Mismatch("id is not shifted by one")
            return left, {**right, "value": {**right["value"], "id": left["value"]["id"]}}

        registered("id_shift", compare)
        return [Entry(match="*/dump", cls="approved", decision="D1", assert_="id_shift")]

    def test_approved_holds(self, id_shift):
        assert not self.judge(id_shift, fake_side(), fake_side(poison=True)).mismatches

    def test_approved_assertion_fails(self, id_shift):
        reasons = {o.reason for o in self.judge(id_shift, fake_side(), fake_side()).mismatches}
        assert reasons == {"approved (D1, id_shift): id is not shifted by one"}

    def test_approved_rest_differs(self, id_shift):
        right = fake_side(poison=True)
        right[0]["value"]["text"] = "changed"
        result = self.judge(id_shift, fake_side(), right)
        assert [(o.key, o.reason) for o in result.mismatches] == [
            ("a/dump", "approved (D1, id_shift): the rest of the record differs")
        ]


class TestEvaluate:
    def test_clean(self):
        code, report = runner.evaluate(
            as_trace(fake_side()), as_trace(fake_side()), [], poison=None
        )
        assert code == runner.EXIT_OK
        assert report.endswith("0 mismatches")
        assert "invariant         2           0" in report

    def test_mismatch(self):
        code, report = runner.evaluate(
            as_trace(fake_side()), as_trace(fake_side(poison=True)), [], poison=None, max_diffs=1
        )
        assert code == runner.EXIT_MISMATCH
        assert "MISMATCH a/dump: invariant: records differ" in report
        assert '-  "id": 1,' in report
        assert '+  "id": 2,' in report
        assert "MISMATCH b/dump" not in report
        assert "1 more mismatches" in report
        assert report.endswith("2 unapproved mismatch(es)")

    def test_poison_detected(self):
        code, _ = runner.evaluate(
            as_trace(fake_side()), as_trace(fake_side(poison=True)), [], poison="right"
        )
        assert code == runner.EXIT_MISMATCH

    def test_poison_not_detected(self):
        """A poisoned side that changes nothing means the harness is blind: fail loudly."""
        code, report = runner.evaluate(
            as_trace(fake_side()), as_trace(fake_side()), [], poison="right"
        )
        assert code == runner.EXIT_POISON_NOT_DETECTED
        assert report.endswith("poison not detected (--poison right)")

    def test_when_uses_header_adapters(self):
        entries = [Entry(match="*", cls="new", decision="D10", when="aiogram4")]
        left, right = as_trace(fake_side()), as_trace(fake_side(), adapter="aiogram4")
        code, _ = runner.evaluate(left, as_trace(fake_side()), entries, poison=None)
        assert code == runner.EXIT_OK  # inactive: both sides are aiogram3
        code, _ = runner.evaluate(left, right, entries, poison=None)
        assert code == runner.EXIT_MISMATCH  # active: left did not fail


class TestSides:
    @pytest.mark.parametrize(
        ("spec", "scheme", "target"),
        [
            ("pypi:aiogram==3.32.0", "pypi", "aiogram==3.32.0"),
            ("pypi:aiogram<4", "pypi", "aiogram<4"),
            ("git:HEAD", "git", "HEAD"),
            ("path:.", "path", "."),
            ("path:C:\\src", "path", "C:\\src"),
        ],
    )
    def test_parse_side(self, spec, scheme, target):
        assert runner.parse_side(spec) == runner.Side(spec, scheme, target)

    @pytest.mark.parametrize("spec", ["aiogram==3.32.0", "pypi:", "svn:trunk", ""])
    def test_parse_side_rejects(self, spec):
        with pytest.raises(HarnessError, match="bad side"):
            runner.parse_side(spec)

    @pytest.mark.parametrize(
        ("version", "adapter"), [("3.33.0", "aiogram3"), ("4.0.0a1", "aiogram4")]
    )
    def test_adapter_for(self, version, adapter):
        assert runner.adapter_for(version) == adapter

    def test_adapter_for_unknown(self):
        with pytest.raises(HarnessError, match="no adapter"):
            runner.adapter_for("2.25.1")

    def test_smoke_side_in_process(self, tmp_path, monkeypatch):
        """The aiogram3 smoke side against this checkout, run in-process (no venv)."""
        import runpy

        out = tmp_path / "t.jsonl"
        for poison, name in ((False, "clean"), (True, "poisoned")):
            argv = [
                "smoke.py",
                "--corpus",
                str(ROOT / "benchmarks" / "corpus"),
                "--out",
                str(out.with_name(f"{name}.jsonl")),
                "--trace-module",
                str(ROOT / "differential" / "trace.py"),
                "--header",
                json.dumps({"adapter": "aiogram3"}),
            ]
            monkeypatch.setattr(sys, "argv", argv + (["--poison"] if poison else []))
            runpy.run_path(
                str(ROOT / "differential" / "sides" / "aiogram3" / "smoke.py"), run_name="__main__"
            )
        clean = trace.read(out.with_name("clean.jsonl"))
        poisoned = trace.read(out.with_name("poisoned.jsonl"))
        assert clean[0]["adapter"] == "aiogram3"
        assert "aiogram" in clean[0]
        assert [record["probe"] for record in clean[1]] == ["decode", "dump"]
        assert clean[1][1]["value"]["message"]["text"] == "hello"
        assert runner.evaluate(clean, clean, [], poison=None)[0] == runner.EXIT_OK
        assert runner.evaluate(clean, poisoned, [], poison="right")[0] == runner.EXIT_MISMATCH


def test_cli_harness_error(capsys):
    assert runner.main(["run", "--kind", "smoke", "--left", "bogus", "--right", "path:."]) == 3
    assert "harness error: bad side" in capsys.readouterr().err


def test_trace_round_trips_unicode_line_separators(tmp_path):
    path = tmp_path / "t.jsonl"
    records = [trace.ok("a", "b", "x y z\x85w\rv")]
    trace.write(path, {}, records)
    assert trace.read(path) == ({}, records)


@pytest.mark.parametrize("key", ["when", "assert"])
def test_manifest_rejects_non_string_values(tmp_path, key):
    text = '[[case]]\nmatch = "a"\nclass = "approved"\ndecision = "D1"\nassert = "json_shaped_extras"\n'
    text = text.replace(f'{key} = "json_shaped_extras"\n', "") + f"{key} = [1]\n"
    with pytest.raises(HarnessError):
        runner.load_manifest(write_manifest(tmp_path, text))


class TestCliExitCodes:
    @pytest.fixture
    def sides(self, monkeypatch, tmp_path):
        monkeypatch.setattr(runner, "STATE", tmp_path)
        traces: list[runner.Trace] = []
        monkeypatch.setattr(runner, "run_side", lambda *args, **kwargs: traces.pop(0))
        return traces

    def run(self, *extra: str) -> int:
        return runner.main(
            ["run", "--kind", "smoke", "--left", "git:HEAD", "--right", "path:.", *extra]
        )

    def test_clean_and_poisoned(self, sides):
        sides.extend([as_trace(fake_side()), as_trace(fake_side())])
        assert self.run() == runner.EXIT_OK
        sides.extend([as_trace(fake_side()), as_trace(fake_side(poison=True))])
        assert self.run("--poison", "right") == runner.EXIT_MISMATCH

    def test_duplicate_record_is_a_harness_error(self, sides, capsys):
        sides.extend([as_trace(fake_side()), as_trace(fake_side() * 2)])
        assert self.run("--poison", "right") == runner.EXIT_HARNESS_ERROR
        assert "twice" in capsys.readouterr().err

    def test_malformed_record_is_a_harness_error(self, sides, capsys):
        sides.extend([as_trace(fake_side()), as_trace([{"probe": "dump"}])])
        assert self.run("--poison", "right") == runner.EXIT_HARNESS_ERROR
        assert "harness error" in capsys.readouterr().err

    def test_usage_error_is_a_harness_error(self, capsys):
        with pytest.raises(SystemExit) as exc:
            runner.main(["run", "--kind", "nope", "--left", "git:HEAD", "--right", "path:."])
        assert exc.value.code == runner.EXIT_HARNESS_ERROR


def test_path_side_always_rebuilds(monkeypatch, tmp_path):
    """uv caches local builds by pyproject only: a fresh venv must not reuse a stale wheel."""
    monkeypatch.setattr(runner, "STATE", tmp_path)
    commands: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> bytes:
        commands.append(cmd)
        if cmd[1] == "venv":
            Path(cmd[-1]).mkdir(parents=True)
        return b""

    monkeypatch.setattr(runner, "_run", fake_run)
    monkeypatch.setattr(runner, "_uv", lambda: "uv")
    side = runner.parse_side(f"path:{ROOT}")
    runner.prepare(side)  # first build into a fresh venv
    runner.prepare(side)  # reuse
    installs = [cmd for cmd in commands if "install" in cmd]
    assert len(installs) == 2
    assert all("--reinstall-package" in cmd for cmd in installs)
