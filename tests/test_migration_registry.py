"""Schema and id rules of aiogram/_migration/registry.toml (A-11, PD-13, PD-33)."""

import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parent.parent
REGISTRY_PATH = Path("aiogram") / "_migration" / "registry.toml"
REGISTRY: dict[str, Any] = tomllib.loads((ROOT / REGISTRY_PATH).read_text(encoding="utf-8"))
ENTRIES: list[dict[str, Any]] = REGISTRY["entry"]

KINDS = {"removal-4.0", "deprecation-4.x", "api-ledger"}
AREAS = {
    "types",
    "dispatcher",
    "filters",
    "middlewares",
    "fsm",
    "errors",
    "client",
    "utils",
    "i18n",
    "packaging",
}
CHANGES = {"removed", "behaviour", "signature", "renamed"}
DETECTIONS = {"definite", "heuristic", "manual"}
CONFIDENCES = {"high", "medium", "low"}
CODEMODS = {"full", "partial", "none"}
SITES = {
    "import",
    "attribute",
    "construction",
    "registration",
    "class-creation",
    "mutation",
    "call",
    "read",
    "none",
}
REQUIRED = {
    "id",
    "kind",
    "title",
    "decisions",
    "area",
    "change",
    "replacement",
    "detection",
    "confidence",
    "codemod",
    "suppress",
    "gate",
    "generated",
    "warn_3x",
}
# PD-33 id blocks: (first, last, kinds allowed in the block)
BLOCKS = (
    (4001, 4699, {"removal-4.0", "deprecation-4.x"}),
    (4700, 4799, {"removal-4.0", "deprecation-4.x"}),
    (4800, 4999, {"api-ledger"}),
)
ID_RE = re.compile(r"AG4\d{3}")
DECISION_RE = re.compile(r"D\d+|PD-\d+|R\d+")
BREAKING_CHANGES = range(1, 25)


def block_of(entry_id: str) -> int:
    number = int(entry_id[2:])
    for index, (first, last, _) in enumerate(BLOCKS):
        if first <= number <= last:
            return index
    pytest.fail(f"{entry_id} is outside every PD-33 block")


def test_header():
    assert REGISTRY["schema"] == 1
    assert set(REGISTRY) == {"schema", "message", "entry"}
    for entry in ENTRIES:
        REGISTRY["message"].format(**entry)


def test_ids_unique_and_sorted():
    ids = [entry["id"] for entry in ENTRIES]
    assert len(ids) == len(set(ids))
    assert ids == sorted(ids)


def test_every_breaking_change_has_an_entry():
    covered = {entry.get("breaking_change") for entry in ENTRIES}
    assert set(BREAKING_CHANGES) - covered == set()


@pytest.mark.parametrize("entry", ENTRIES, ids=[entry["id"] for entry in ENTRIES])
def test_entry(entry: dict[str, Any]):
    kind = entry["kind"]
    allowed = REQUIRED | {"breaking_change"}
    allowed |= {"fields"} if kind == "api-ledger" else set()
    allowed |= {"removal"} if kind == "deprecation-4.x" else set()
    assert REQUIRED <= entry.keys() <= allowed, entry.keys() ^ REQUIRED

    assert ID_RE.fullmatch(entry["id"])
    assert kind in KINDS
    assert kind in BLOCKS[block_of(entry["id"])][2]
    assert entry["title"]
    assert entry["replacement"]
    assert entry["decisions"]
    assert all(DECISION_RE.fullmatch(decision) for decision in entry["decisions"])
    assert entry["area"] in AREAS
    assert entry["change"] in CHANGES
    assert entry["detection"] in DETECTIONS
    assert entry["confidence"] in CONFIDENCES
    assert entry["codemod"] in CODEMODS
    assert entry["suppress"] == f"aiogram: ignore[{entry['id']}]"
    assert isinstance(entry["gate"], bool)
    assert entry["generated"] is (kind == "api-ledger")
    if "breaking_change" in entry:
        assert entry["breaking_change"] in BREAKING_CHANGES

    if kind == "api-ledger":
        assert isinstance(entry["fields"], list)
        assert all(isinstance(name, str) and name for name in entry["fields"])
    if kind == "deprecation-4.x":
        assert set(entry["removal"]) == {"deprecated_in", "earliest_removal"}
        assert all(entry["removal"].values())

    warn = entry["warn_3x"]
    assert set(warn) == {"site", "target", "since"}
    assert warn["site"] in SITES
    assert bool(warn["target"]) is (warn["site"] != "none")
    assert isinstance(warn["since"], str)


def test_loads_without_importing_aiogram():
    code = (
        "import pathlib, sys, tomllib\n"
        f"tomllib.loads(pathlib.Path({str(REGISTRY_PATH)!r}).read_text(encoding='utf-8'))\n"
        "assert 'aiogram' not in sys.modules\n"
    )
    subprocess.run([sys.executable, "-I", "-c", code], cwd=ROOT, check=True)


def _git(*args: str) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def test_append_only_against_previous_release():
    tag = _git("describe", "--tags", "--abbrev=0", "--match", "v[0-9]*")
    if tag is None:
        pytest.skip("no release tag available")
    old_text = _git("show", f"{tag.strip()}:{REGISTRY_PATH.as_posix()}")
    if old_text is None:
        pytest.skip(f"{tag.strip()} has no {REGISTRY_PATH.as_posix()}")

    old_ids = [entry["id"] for entry in tomllib.loads(old_text)["entry"]]
    assert_append_only(old_ids, [entry["id"] for entry in ENTRIES])


def assert_append_only(old_ids: list[str], new_ids: list[str]) -> None:
    assert set(old_ids) - set(new_ids) == set(), "ids are never removed"
    for index in range(len(BLOCKS)):
        old_block = [i for i in old_ids if block_of(i) == index]
        added = [i for i in new_ids if block_of(i) == index and i not in old_ids]
        if old_block and added:
            assert min(added) > max(old_block), "new ids are appended after the block's last id"


@pytest.mark.parametrize(
    ("old", "new", "ok"),
    [
        (["AG4001", "AG4700"], ["AG4001", "AG4002", "AG4700", "AG4701", "AG4800"], True),
        (["AG4001", "AG4002"], ["AG4002"], False),  # removed
        (["AG4001", "AG4003"], ["AG4001", "AG4002", "AG4003"], False),  # gap backfilled
        (["AG4701"], ["AG4700", "AG4701"], False),  # gap backfilled in the 3.x block
    ],
)
def test_append_only_rule(old: list[str], new: list[str], ok: bool):
    if ok:
        assert_append_only(old, new)
    else:
        with pytest.raises(AssertionError):
            assert_append_only(old, new)
