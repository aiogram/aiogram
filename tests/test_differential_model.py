"""The model kind of the differential harness (A-08): the aiogram3 side in-process and its comparators."""

import fnmatch
import json
import platform
import runpy
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
if not (ROOT / "differential").is_dir():  # sdist: differential/ is not shipped
    pytest.skip("differential/ is not part of this checkout", allow_module_level=True)

from differential import runner, trace  # noqa: E402
from differential.runner import Mismatch  # noqa: E402

CORPUS = ROOT / "benchmarks" / "corpus"
MANIFEST = ROOT / "differential" / "manifests" / "model.toml"
ACCESS = ROOT / "differential" / "manifests" / "model.access.toml"
SIDE = ROOT / "differential" / "sides" / "aiogram3" / "model.py"


def update_inputs() -> list[str]:
    manifest = tomllib.loads((CORPUS / "MANIFEST.toml").read_text(encoding="utf-8"))
    return [item["id"] for item in manifest["input"] if item["kind"] == "update"]


def run_side(out: Path, monkeypatch: pytest.MonkeyPatch, *, poison: bool) -> runner.Trace:
    argv = [
        "model.py",
        "--corpus",
        str(CORPUS),
        "--out",
        str(out),
        "--trace-module",
        str(ROOT / "differential" / "trace.py"),
        "--header",
        json.dumps({"adapter": "aiogram3"}),
    ]
    monkeypatch.setattr(sys, "argv", argv + (["--poison"] if poison else []))
    runpy.run_path(str(SIDE), run_name="__main__")
    return trace.read(out)


@pytest.fixture(scope="module")
def traces(tmp_path_factory: pytest.TempPathFactory) -> dict[str, runner.Trace]:
    out = tmp_path_factory.mktemp("model")
    with pytest.MonkeyPatch.context() as monkeypatch:
        return {
            name: run_side(out / f"{name}.jsonl", monkeypatch, poison=poison)
            for name, poison in (("clean", False), ("poisoned", True))
        }


@pytest.fixture(scope="module")
def records(traces: dict[str, runner.Trace]) -> dict[str, dict[str, Any]]:
    return {f"{r['case']}/{r['probe']}": r for r in traces["clean"][1]}


class TestSide:
    def test_every_update_input_has_every_probe(self, records):
        probes = ("decode.json", "decode.dict", *runpy.run_path(str(SIDE))["UPDATE_PROBES"])
        for input_id in update_inputs():
            for probe in probes:
                assert f"model.{input_id}/{probe}" in records

    def test_access_lists_cover_the_corpus(self):
        access = tomllib.loads(ACCESS.read_text(encoding="utf-8"))
        assert set(access) == {"access"}
        assert set(access["access"]) == set(update_inputs())

    def test_decode_outcome_matches_on_3x(self, records):
        manifest = tomllib.loads((CORPUS / "MANIFEST.toml").read_text(encoding="utf-8"))
        for item in manifest["input"]:
            if item["kind"] != "update":
                continue
            decode = records[f"model.{item['id']}/decode.json"]
            event = records[f"model.{item['id']}/event"]
            outcome = "ok"
            for record in (decode, event):
                if not record["ok"]:
                    outcome = record["error"]["type"]
                    break
            assert outcome == item["on_3x"], item["id"]

    def test_failed_decode_fails_every_later_probe(self, records):
        record = records["model.update.unknown-tag/dump.python"]
        assert record["error"] == {"type": "DecodeFailed", "attrs": {}}

    def test_validation_error_attrs_have_no_messages(self, records):
        attrs = records["model.update.unknown-tag/decode.json"]["error"]["attrs"]
        assert attrs == {
            "error_count": 1,
            "errors": [{"type": "union_tag_invalid", "loc": ["chat_member", "new_chat_member"]}],
        }

    def test_access(self, records):
        value = records["model.update.text.small/access"]["value"]
        assert value["message.text"] == {"ok": True, "value": "hello"}
        assert value["message.entities"] == {"ok": True, "value": None}
        value = records["model.update.media.large/access"]["value"]
        assert value["channel_post.caption_entities[119].length"]["ok"] is True

    def test_access_records_a_missing_attribute(self, records):
        value = records["model.update.unknown-type/access"]["value"]
        assert value["future_update"]["ok"] is True  # 3.x: an extra, readable as an attribute
        side = runpy.run_path(str(SIDE))
        assert side["access"](object(), ["nope"]) == {
            "nope": {"ok": False, "error": "AttributeError"}
        }

    def test_dump_names(self, records):
        assert (
            "from_user"
            in records["model.update.inline-query/dump.python"]["value"]["inline_query"]
        )
        assert "from" in records["model.update.inline-query/dump.wire"]["value"]["inline_query"]
        wire = records["model.construct.Message/dump.wire"]["value"]
        assert wire == records["model.construct.Message.wire_kwargs/dump.wire"]["value"]
        assert "from" in wire

    def test_construct_keeps_default_placeholders(self, records):
        value = records["model.construct.SendMessage/dump.python"]["value"]
        assert value["parse_mode"]["__kind__"] == "repr"
        assert value["parse_mode"]["repr"] == "<Default('parse_mode')>"

    @pytest.mark.parametrize(
        ("case", "observed"),
        [
            ("eq_across_bots", False),
            ("dump_json_type", "str"),
            ("model_extra_only_unknown", {"future_field": 1}),
            (
                "exclude_none_nested_null",
                {"first_name": "Ada", "future": {"kept": None, "n": 1}, "id": 1, "is_bot": False},
            ),
            ("pickle_bound", {"bound": "TypeError", "unbound": True}),
            (
                "as_keeps_nested_bot",
                {
                    "returns_self": True,
                    "original": "other",
                    "view": "other",
                    "view_child": "bot",
                    "root": "bot",
                },
            ),
            ("builder_export_copy", {"assigned": "changed", "builder": "a"}),
        ],
    )
    def test_codex11_observation(self, records, case, observed):
        """codex-review.md section 11 and the 19 header, reproduced on this checkout."""
        if case == "pickle_bound" and platform.python_implementation() == "PyPy":
            observed = {**observed, "bound": "ok"}  # PyPy pickles the bot's SSLContext
        record = records[f"model.codex11.{case}/observe"]
        assert record["ok"] is True
        assert record["value"] == observed

    def test_clean_and_poisoned(self, traces):
        entries = runner.load_manifest(MANIFEST)
        clean, poisoned = traces["clean"], traces["poisoned"]
        assert runner.evaluate(clean, clean, entries, poison=None)[0] == runner.EXIT_OK
        code, report = runner.evaluate(clean, poisoned, entries, poison="right")
        assert code == runner.EXIT_MISMATCH
        assert "dump.python: invariant" in report
        assert "dump.wire: invariant" in report

    def test_manifest_entries_match_recorded_cases(self, records):
        for entry in runner.load_manifest(MANIFEST):
            if entry.assert_ == "collections_are_tuples":  # no probe yet, B plans add it
                continue
            assert any(fnmatch.fnmatchcase(key, entry.match) for key in records), entry.match


def ok(value: Any) -> dict[str, Any]:
    return trace.ok("c", "p", value)


def err(type_: str, attrs: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"case": "c", "probe": "p", "ok": False, "error": {"type": type_, "attrs": attrs or {}}}


def judge(name: str, left: dict[str, Any], right: dict[str, Any]) -> None:
    """Run a comparator the way the runner does: its assertion, then the rest of the record."""
    entry = runner.Entry(match="*", cls="approved", decision="X", assert_=name)
    reason = runner._judge(entry, left, right)
    if reason is not None:
        raise Mismatch(reason)


RECURSION = {"error_count": 1, "errors": [{"type": "recursion_loop", "loc": ["message"]}]}
DEPTH = {"error_count": 2, "errors": [{"type": "recursion_depth_exceeded", "loc": []}]}
VIEW_3X = {
    "returns_self": True,
    "original": "other",
    "view": "other",
    "view_child": "bot",
    "root": "bot",
}
VIEW_4X = {
    "returns_self": False,
    "original": "bot",
    "view": "other",
    "view_child": "other",
    "root": "bot",
}
DUMP_3X = {"type": "str", "value": {"from_user": None, "id": 1}, "wire": {"id": 1}}
DUMP_4X = {"type": "str", "value": {"id": 1}, "wire": {"id": 1}}


class TestComparators:
    @pytest.mark.parametrize(
        ("name", "left", "right"),
        [
            ("equality_ignores_bot", ok(False), ok(True)),
            ("wire_names_in_dump_json", ok(DUMP_3X), ok(DUMP_4X)),
            ("json_shaped_extras", ok({"future": 1}), err("TypeError")),
            ("hashable_when_fields_are", err("TypeError"), ok("int")),
            ("hashable_when_fields_are", ok("int"), ok("int")),
            ("immutable_types", ok({"text": "b"}), err("AttributeError")),
            ("immutable_types", err("ValidationError"), err("AttributeError")),
            ("replace_validates", ok({"type": "str", "update_id": "x"}), err("ValidationError")),
            ("as_returns_new_view", ok(VIEW_3X), ok(VIEW_4X)),
            ("nesting_limit_on_dict_path", ok({"type": "Update"}), err("ValidationError", DEPTH)),
            (
                "nesting_limit_on_dict_path",
                err("ValidationError", RECURSION),
                err("ValidationError", DEPTH),
            ),
        ],
    )
    def test_holds(self, name, left, right):
        judge(name, left, right)

    @pytest.mark.parametrize(
        ("name", "left", "right", "why"),
        [
            ("equality_ignores_bot", ok(True), ok(True), "left does not"),
            ("equality_ignores_bot", ok(False), ok(False), "right does not"),
            ("equality_ignores_bot", ok(False), err("TypeError"), "right does not"),
            ("wire_names_in_dump_json", err("PydanticSerializationError"), ok(DUMP_4X), "failed"),
            ("wire_names_in_dump_json", ok(DUMP_3X), ok(DUMP_3X), "not left's wire"),
            (
                "wire_names_in_dump_json",
                ok(DUMP_3X),
                ok({**DUMP_4X, "type": "bytes"}),
                "not left's",
            ),
            ("json_shaped_extras", err("TypeError"), err("TypeError"), "left rejected"),
            ("json_shaped_extras", ok({}), err("ValueError"), "TypeError"),
            ("hashable_when_fields_are", ok("int"), err("TypeError"), "right is not"),
            ("hashable_when_fields_are", err("ValueError"), ok("int"), "left neither"),
            ("immutable_types", ok({"text": "b"}), ok({"text": "b"}), "allowed"),
            ("replace_validates", ok({"type": "int"}), err("ValidationError"), "left validated"),
            ("replace_validates", ok({"type": "str"}), ok({"type": "str"}), "accepted"),
            (
                "as_returns_new_view",
                ok({**VIEW_3X, "returns_self": False}),
                ok(VIEW_4X),
                "in place",
            ),
            ("as_returns_new_view", ok(VIEW_3X), ok(VIEW_3X), "not a new view"),
            ("nesting_limit_on_dict_path", ok({}), ok({}), "right did not"),
            (
                "nesting_limit_on_dict_path",
                ok({}),
                err("ValidationError", {"errors": [{"type": "missing", "loc": []}]}),
                "right did not",
            ),
            ("nesting_limit_on_dict_path", ok({}), err("ValidationError", {}), "right did not"),
            (
                "nesting_limit_on_dict_path",
                err("TypeError"),
                err("ValidationError", DEPTH),
                "left",
            ),
        ],
    )
    def test_fails(self, name, left, right, why):
        with pytest.raises(Mismatch, match=why):
            judge(name, left, right)
