"""The routing oracle (A-10): the aiogram3 routing side, run in-process, and its comparators."""

import asyncio
import json
import logging
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

Record = dict[str, Any]
CORPUS = ROOT / "benchmarks" / "corpus"
SIDE = ROOT / "differential" / "sides" / "aiogram3" / "routing.py"
MANIFEST = runner.load_manifest(ROOT / "differential" / "manifests" / "routing.toml")
TOPOLOGIES = {
    item["id"]: tomllib.loads((CORPUS / item["path"]).read_text(encoding="utf-8"))
    for item in tomllib.loads((CORPUS / "MANIFEST.toml").read_text(encoding="utf-8"))["input"]
    if item["kind"] == "routing"
}


def run_side(tmp_path: Path, *, poison: bool) -> runner.Trace:
    out = tmp_path / f"{'poisoned' if poison else 'clean'}.jsonl"
    argv = [
        "routing.py",
        "--corpus",
        str(CORPUS),
        "--out",
        str(out),
        "--trace-module",
        str(ROOT / "differential" / "trace.py"),
        "--header",
        json.dumps({"adapter": "aiogram3"}),
    ]
    saved = sys.argv
    sys.argv = argv + (["--poison"] if poison else [])
    try:
        runpy.run_path(str(SIDE), run_name="__main__")
    finally:
        sys.argv = saved
        logging.disable(logging.NOTSET)  # the side silences aiogram's logging in its process
    return trace.read(out)


@pytest.fixture(scope="module")
def traces(tmp_path_factory: pytest.TempPathFactory) -> dict[str, runner.Trace]:
    tmp_path = tmp_path_factory.mktemp("routing")
    return {"clean": run_side(tmp_path, poison=False), "poisoned": run_side(tmp_path, poison=True)}


@pytest.fixture(scope="module")
def records(traces: dict[str, runner.Trace]) -> dict[str, Record]:
    return {f"{r['case']}/{r['probe']}": r for r in traces["clean"][1]}


def require_d12_injection(records: dict[str, Record]) -> None:
    """Skip a check that needs a 3.x record with the D12 keys.

    The side runs in-process against this checkout, and on dev-4.x E-01 has already removed the
    ``event_from_user`` / ``event_chat`` / ``event_thread_id`` injection (D12).
    """
    kwargs = records["routing.middleware.outer.no-match.polling.fsm-off.first/kwargs"]
    if not any(key in e["data"] for e in kwargs["value"] for key in runner.D12_KEYS):
        pytest.skip("this checkout does not inject the D12 keys; the check needs a 3.x record")


def cases(topology_id: str, topology: dict[str, Any]) -> list[tuple[str, list[dict[str, Any]]]]:
    """(case, events) per feed, fsm variant and batch, as the side names them."""
    out = []
    variants = topology.get("variants", {})
    for feed in variants.get("feed", ["polling"]):
        for fsm in variants.get("fsm", ["off"]):
            batches: list[list[dict[str, Any]]] = []
            for event in topology["event"]:
                group = event.get("group")
                if batches and group is not None and batches[-1][0].get("group") == group:
                    batches[-1].append(event)
                else:
                    batches.append([event])
            for batch in batches:
                name = batch[0].get("group", batch[0]["name"])
                out.append((f"{topology_id}.{feed}.fsm-{fsm}.{name}", batch))
    return out


class TestSide:
    def test_header(self, traces):
        header = traces["clean"][0]
        assert header["adapter"] == "aiogram3"
        assert header["aiogram"]

    @pytest.mark.parametrize("topology_id", sorted(TOPOLOGIES))
    def test_every_event_is_traced_and_lands_on_expect(self, records, topology_id):
        if topology_id == "routing.kwargs.event-from-user":
            require_d12_injection(records)
        topology = TOPOLOGIES[topology_id]
        for case, batch in cases(topology_id, topology):
            for probe in ("trace", "kwargs", "threads", "result"):
                assert records[f"{case}/{probe}"]["ok"] is True, (case, probe)
            outcomes = records[f"{case}/result"]["value"]
            entries = records[f"{case}/trace"]["value"]
            for index, event in enumerate(batch):
                outcome, expect = outcomes[index], event["expect"]
                if expect == "unhandled":
                    # feed_webhook_update answers None for anything but a Bot API method
                    unhandled = None if ".webhook.fsm-" in case else "UNHANDLED"
                    assert outcome == {"returned": unhandled}, case
                    assert not [e for e in entries if e["kind"] == "handler"], case
                elif expect == "raised":
                    assert "raised" in outcome, case
                else:
                    called = {
                        e["component"]
                        for e in entries
                        if e["update"] == index
                        and e["kind"] in {"handler", "error"}
                        and not (isinstance(e["result"], dict) and "raised" in e["result"])
                    }
                    assert expect in called or outcome == {"returned": expect}, (case, event)

    @pytest.mark.parametrize("topology_id", sorted(TOPOLOGIES))
    def test_used_update_types(self, records, topology_id):
        for fsm in TOPOLOGIES[topology_id].get("variants", {}).get("fsm", ["off"]):
            used = records[f"{topology_id}.polling.fsm-{fsm}/used_update_types"]["value"]
            assert "message" in used

    def test_clean_run_equals_itself_under_the_manifest(self, traces):
        code, _ = runner.evaluate(traces["clean"], traces["clean"], MANIFEST, poison=None)
        assert code == runner.EXIT_OK

    def test_poison_is_detected(self, traces):
        code, report = runner.evaluate(
            traces["clean"], traces["poisoned"], MANIFEST, poison="right"
        )
        assert code == runner.EXIT_MISMATCH, report


class TestCodexR09Probes:
    """codex-review §11: the three R09 observations, on the real Router.message observer."""

    @staticmethod
    def data_of(records: Record, topology: str, component: str) -> dict[str, Any]:
        for fsm in ("on", "off"):
            entries = records[f"routing.r09.{topology}.polling.fsm-{fsm}.first/kwargs"]["value"]
            (entry,) = [e for e in entries if e["component"] == component]
            yield entry["data"]

    def test_failed_candidate_filter_data_is_not_visible(self, records):
        for data in self.data_of(records, "failed-filter-data", "h2"):
            assert "db" not in data

    def test_filter_data_after_skip_handler_is_visible(self, records):
        for data in self.data_of(records, "skip-after-filters", "h2"):
            assert data["db"] == "h1.f0"

    def test_inner_middleware_write_then_skip_is_visible(self, records):
        for data in self.data_of(records, "inner-write-then-skip", "h2"):
            assert data["mw"] == "m1"

    def test_the_inner_middleware_is_inherited_from_the_parent_router(self, records):
        topology = TOPOLOGIES["routing.r09.inner-write-then-skip"]
        assert [r["name"] for r in topology["router"] if r.get("inner_middlewares")] == ["dp"]
        entries = records["routing.r09.inner-write-then-skip.polling.fsm-off.first/trace"]["value"]
        assert [e["component"] for e in entries if e["kind"] == "handler"] == ["h2"]
        assert {e["router"] for e in entries if e["kind"] == "handler"} == {"r1"}

    def test_shallow_copies_share_a_nested_value(self, records):
        entries = records["routing.r09.scopes.polling.fsm-off.first/kwargs"]["value"]
        (h3,) = [e for e in entries if e["component"] == "h3"]
        assert h3["data"]["bag"] == {"from": "dp.m0", "by": "h1.f1"}
        assert {"a", "b", "scope"}.isdisjoint(h3["data"])  # a sibling router sees none of r1's


# ------------------------------------------------------------------------------------------------
# Comparators: each one against the real 3.x record and a hand-made 4.0 record.
# ------------------------------------------------------------------------------------------------


def judge(left: Record, right: Record) -> str | None:
    """The runner's verdict for the pair under the shipped manifest, a 4.0 right side."""
    key = f"{left['case']}/{left['probe']}"
    entry = runner.classify(key, MANIFEST, {"aiogram3", "aiogram4"})
    return runner.compare([left], [right], [entry], {"aiogram3", "aiogram4"}).outcomes[0].reason


def without(record: Record, drop) -> Record:
    return {**record, "value": [e for e in record["value"] if not drop(e)]}


def strip_d12(record: Record) -> Record:
    keys = set(runner.D12_KEYS)
    if record["probe"] != "kwargs":
        return record
    return {
        **record,
        "value": [
            {**e, "data": {k: v for k, v in e["data"].items() if k not in keys}}
            for e in record["value"]
        ],
    }


NO_MATCH = "routing.middleware.outer.no-match.polling.fsm-off.first"


class TestComparators:
    def test_all_seven_are_real(self):
        for name in (
            "outer_middleware_skipped_without_handler",
            "compiled_rejector_skips_handler",
            "errors_bubble_to_raising_router",
            "sync_filters_inline",
            "event_isolation_default",
            "routing_snapshot_per_runner",
            "event_context_only_kwargs",
        ):
            assert runner.COMPARATORS[name].__name__ == name

    def test_identical_right_is_approved_where_4x_may_keep_3x_behaviour(self, records):
        """Every approved difference is optional, except where the decision forces one."""
        forced = ("routing.errors.", "routing.isolation.", "routing.snapshot.register-middleware")
        for key, left in records.items():
            if (
                key.startswith(forced)
                or key.startswith("routing.snapshot.include-router")
                and (".first/" in key)
            ):
                continue
            right = strip_d12(left)
            if left["probe"] == "threads":
                right = {
                    **left,
                    "value": [
                        {**e, "on_loop": True} if e["kind"] == "filter" else e
                        for e in left["value"]
                    ],
                }
            assert judge(left, right) is None, key

    def test_d12_keys_still_injected(self, records):
        require_d12_injection(records)
        left = records[f"{NO_MATCH}/kwargs"]
        assert "right still injects" in judge(left, left)

    def test_d34_sync_filters_on_loop(self, records):
        left = records["routing.filters.sync.work.polling.fsm-off.first/threads"]
        assert [e["on_loop"] for e in left["value"]] == [False, True, False]
        inline = [{**e, "on_loop": True} if e["kind"] == "filter" else e for e in left["value"]]
        assert judge(left, {**left, "value": inline}) is None
        assert judge(left, left) is not None  # 4.0 must move the sync filter
        all_inline = [{**e, "on_loop": True} for e in left["value"]]
        assert judge(left, {**left, "value": all_inline}) is not None  # handler stays threaded

    @pytest.mark.parametrize("probe", ["trace", "kwargs"])
    def test_d111_skips_routers_without_a_called_handler(self, records, probe):  # noqa: PLR0914
        left = records[f"{NO_MATCH}/{probe}"]
        skipped = strip_d12(without(left, lambda e: "r1" in e["path"]))
        assert judge(left, skipped) is None
        both = strip_d12(without(left, lambda e: "r1" in e["path"] or "r2" in e["path"]))
        assert judge(left, both) is not None  # r2's candidate survives the rejectors: entered
        handled = strip_d12(without(left, lambda e: "r3" in e["path"]))
        assert judge(left, handled) is not None  # r3 called h3: never skipped
        if probe == "trace":
            exit_only = strip_d12(
                without(left, lambda e: e["component"] == "r1.m0" and e["result"] != "enter")
            )
            assert judge(left, exit_only) is not None  # a router is skipped whole or not at all

    def test_bc13_skips_user_filters_of_rejected_candidates(self, records):
        for name in ("command", "magic-eq"):
            left = records[f"routing.rejector.{name}.polling.fsm-off.first/trace"]
            assert [e["component"] for e in left["value"]] == ["h1.f0", "h2"]
            assert judge(left, without(left, lambda e: e.get("owner") == "h1")) is None
            assert judge(left, without(left, lambda e: e["component"] == "h2")) is not None

    def test_d48_errors_bubble_from_the_raising_router(self, records):
        for name in ("handler", "middleware", "filter"):
            case = f"routing.errors.{name}.polling.fsm-off.first"
            left = records[f"{case}/trace"]
            errors = [e for e in left["value"] if e["kind"] == "error"]
            assert [e["component"] for e in errors] == ["dp.e0", "r1.e0", "r2.e0"]
            rest = [e for e in left["value"] if e["kind"] != "error"]
            by_id = {e["component"]: e for e in errors}
            bubbled = {**left, "value": [*rest, by_id["r1.e0"], by_id["dp.e0"]]}
            assert judge(left, bubbled) is None
            assert judge(left, left) is not None  # the sibling r2 no longer catches it
            kwargs = records[f"{case}/kwargs"]
            k_rest = [e for e in kwargs["value"] if e["kind"] != "error"]
            k_by_id = {e["component"]: e for e in kwargs["value"] if e["kind"] == "error"}
            k_bubbled = strip_d12(
                {**kwargs, "value": [*k_rest, k_by_id["r1.e0"], k_by_id["dp.e0"]]}
            )
            assert judge(kwargs, k_bubbled) is None
            result = records[f"{case}/result"]
            message = f"{name} failed"
            escaped = {
                **result,
                "value": [{"raised": {"type": "OracleError", "message": message}}],
            }
            assert judge(result, escaped) is None  # r1 and dp decline: the original escapes
            assert judge(result, result) is not None  # the sibling r2 no longer handles it
            other = {**result, "value": [{"raised": {"type": "RuntimeError", "message": message}}]}
            assert judge(result, other) is not None
            assert judge(result, {**result, "value": [{"returned": "dp.e0"}]}) is not None

    def test_d48_right_reaching_an_unseen_handler(self, records):
        kwargs = records["routing.errors.handler.polling.fsm-off.first/kwargs"]
        ghost = {"component": "r11.e0", "kind": "error", "update": 0, "path": [], "data": {}}
        right = strip_d12({**kwargs, "value": [*kwargs["value"], ghost]})
        assert judge(kwargs, right) is not None

    @pytest.mark.parametrize("probe", ["kwargs", "threads"])
    def test_d48_the_sibling_alone_is_not_approved_on_any_probe(self, records, probe):
        left = records[f"routing.errors.handler.polling.fsm-off.first/{probe}"]
        sibling = without(left, lambda e: e["kind"] == "error" and e["component"] != "r2.e0")
        assert judge(left, strip_d12(sibling)) is not None
        by_id = {e["component"]: e for e in left["value"] if e["kind"] == "error"}
        rest = [e for e in left["value"] if e["kind"] != "error"]
        bubbled = strip_d12({**left, "value": [*rest, by_id["r1.e0"], by_id["dp.e0"]]})
        if probe == "threads":
            bubbled["value"] = [
                {**e, "on_loop": True} if e["kind"] == "filter" else e for e in bubbled["value"]
            ]
        assert judge(left, bubbled) is None

    def test_d28_isolation_serialises_one_key(self, records):
        left = records["routing.isolation.same-key.polling.fsm-on.pair/trace"]
        assert [e["update"] for e in left["value"]] == [0, 1, 0]
        serial = sorted(left["value"], key=lambda e: e["update"])
        assert judge(left, {**left, "value": serial}) is None
        assert judge(left, left) is not None
        reversed_order = sorted(left["value"], key=lambda e: -e["update"])
        assert judge(left, {**left, "value": reversed_order}) is not None

    def test_d114_late_components_apply_from_the_next_update(self, records):
        case = "routing.snapshot.register-middleware.polling.fsm-off"
        first, second = records[f"{case}.first/trace"], records[f"{case}.second/trace"]
        assert any(e.get("registers") == "late.m0" for e in first["value"])
        late = [e for e in second["value"] if e["component"] == "late.m0"]
        assert late and not [e for e in late if "late" in e]  # registered by an earlier case
        assert judge(first, without(first, lambda e: e.get("late") == "late.m0")) is None
        assert judge(second, without(second, lambda e: e["component"] == "late.m0")) is not None
        assert judge(second, second) is None
        unhandled = [{"returned": "UNHANDLED"}]
        for case, approved in (
            ("include-router.polling.fsm-off.first", True),  # only the late router matched
            ("include-router.polling.fsm-off.second", False),  # r3 is part of the routing now
            ("register-middleware.polling.fsm-off.first", False),  # h2 existed before
        ):
            result = records[f"routing.snapshot.{case}/result"]
            assert (judge(result, {**result, "value": unhandled}) is None) is approved, case
        result = records["routing.snapshot.include-router.polling.fsm-off.first/result"]
        assert judge(result, {**result, "value": [{"returned": "h1"}]}) is not None

    def test_d114_threads_drop_the_late_handler(self, records):
        left = records["routing.snapshot.include-router.polling.fsm-off.first/threads"]
        assert [e["component"] for e in left["value"]] == ["h1.f0", "h3"]
        assert judge(left, without(left, lambda e: e["component"] == "h3")) is None

    def test_d114_the_registering_router_survives_the_rejectors(self, records):
        """4.0 must enter r1 for the registration to happen at all (PD-19)."""
        for name in ("include-router", "register-middleware"):
            meta = records[f"routing.snapshot.{name}.polling.fsm-off.first/trace"]["meta"]
            (h1,) = [c for c in meta["candidates"] if c["handler"] == "h1"]
            assert h1["rejected"] is False
            assert h1["path"] == ["dp", "r1"]

    def test_d111_applies_to_the_bench_topologies(self, records):
        left = records["routing.52-handlers.polling.fsm-off.unhandled/trace"]
        assert left["value"]  # 3.x enters every router's outer chain
        assert all(c["rejected"] for c in left["meta"]["candidates"])
        right = without(left, lambda e: e.get("observer") != "update")
        assert judge(left, right) is None

    def test_d12_handler_asking_for_event_from_user(self, records):
        require_d12_injection(records)
        case = "routing.kwargs.event-from-user.polling.fsm-off.first"
        kwargs, result = records[f"{case}/kwargs"], records[f"{case}/result"]
        assert judge(kwargs, without(kwargs, lambda e: e["kind"] == "handler")) is None  # DI error
        assert judge(kwargs, strip_d12(kwargs)) is None  # ran without it
        assert judge(kwargs, kwargs) is not None  # still injected
        error = {**result, "value": [{"raised": {"type": "TypeError", "message": "x"}}]}
        assert judge(result, error) is None
        assert judge(result, {**result, "value": [{"returned": "other"}]}) is not None
        traced = records[f"{case}/trace"]
        assert judge(traced, without(traced, lambda e: e["kind"] == "handler")) is None
        # only the handler that asks for event_from_user may go missing
        other = {**traced, "meta": {**traced["meta"], "d12_params": []}}
        assert judge(other, without(traced, lambda e: e["kind"] == "handler")) is not None
        assert judge({**result, "meta": {**result["meta"], "d12_params": []}}, error) is not None

    def test_value_that_is_not_a_list(self, records):
        left = records[f"{NO_MATCH}/trace"]
        with pytest.raises(Mismatch, match="not a list"):
            runner.COMPARATORS["outer_middleware_skipped_without_handler"](
                left, {**left, "value": {}}
            )

    def test_failed_probe_is_compared_as_is(self, records):
        left = {**records[f"{NO_MATCH}/trace"], "ok": False, "value": None}
        assert runner.COMPARATORS["sync_filters_inline"](left, left) == (left, left)

    def test_errors_without_a_raise(self, records):
        left = records["routing.errors.handler.polling.fsm-off.first/trace"]
        broken = {**left, "meta": {**left["meta"], "errors": []}}
        assert "nothing raised" in judge(broken, broken)


class TestBuilder:
    @pytest.fixture(scope="class")
    def side(self) -> dict[str, Any]:
        return runpy.run_path(str(SIDE), run_name="routing_side")

    @pytest.mark.parametrize(
        ("factory", "spec"),
        [
            ("make_filter", {"id": "f", "kind": "bogus"}),
            ("make_middleware", {"id": "m", "kind": "bogus"}),
        ],
    )
    def test_unknown_kind(self, side, factory, spec):
        where = side["Where"](spec, "x", "dp", ["dp"])
        args = (spec, where) if factory == "make_filter" else (spec, where, None)
        with pytest.raises(ValueError, match="unknown"):
            side[factory](*args)

    def test_reused_event_or_group_name(self, side):
        topology = {
            "router": [{"name": "dp"}],
            "event": [
                {"name": "a", "group": "g", "update": "update.text.small"},
                {"name": "b", "update": "update.text.small"},
                {"name": "c", "group": "g", "update": "update.text.small"},
            ],
        }
        payloads = {"update.text.small": (CORPUS / "wire" / "update.text.small.json").read_bytes()}
        run = side["run_topology"](trace, "t", topology, payloads, poison=False)
        with pytest.raises(ValueError, match="'g' reused"):
            asyncio.run(run)

    def test_unsupported_params(self, side):
        spec = {"id": "h", "params": ["event_chat"]}
        with pytest.raises(ValueError, match="unsupported params"):
            side["make_handler"](spec, side["Where"](spec, "handler", "dp", ["dp"]), None)

    def test_unknown_late_registration(self, side):
        build = side["Builder"]({"router": [{"name": "dp"}]}, fsm=False)
        with pytest.raises(ValueError, match="unknown late registration"):
            build.register_late({"id": "x", "what": "bogus"})
        assert build.register_late({"id": "x", "what": "bogus"}) is False  # once per id

    def test_poison_swaps_two_handlers(self, side):
        topology = {
            "router": [
                {"name": "dp", "handler": [{"event": "message"}, {"event": "message"}]},
            ]
        }
        build = side["Builder"](topology, fsm=False)
        before = list(build.dp.message.handlers)
        build.poison()
        assert build.dp.message.handlers == before[::-1]


@pytest.mark.parametrize("topology_id", sorted(TOPOLOGIES))
def test_bench_builds_every_topology_not_marked_bench_false(topology_id):
    """The A-05 bench builds every routing topology without `bench = false`."""
    from benchmarks.adapters.aiogram3 import build_dispatch

    topology = TOPOLOGIES[topology_id]
    if topology.get("bench", True) is False:
        assert topology_id not in BENCH_CASES
        return
    assert topology_id in BENCH_CASES
    updates = {
        event["update"]: json.loads((CORPUS / "wire" / f"{event['update']}.json").read_bytes())
        for event in topology["event"]
    }
    build_dispatch(topology, updates, fsm=True)


def _bench_cases() -> set[str]:
    from benchmarks.cases import dispatch  # noqa: F401 - registers the routing cases
    from benchmarks.harness import REGISTRY

    return set(REGISTRY)


BENCH_CASES = _bench_cases()
