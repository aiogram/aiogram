"""C-26: the 3.x removal inventory and signature tables (aiogram/_migration/data/, read by path)."""

from __future__ import annotations

import importlib.util
import inspect
import json
import re
import sys
import tomllib
from pathlib import Path

import pytest

from aiogram import Bot, Router
from aiogram.methods import TelegramMethod

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "aiogram" / "_migration" / "data"
REGISTRY = ROOT / "aiogram" / "_migration" / "registry.toml"


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


inventory_script = _script("butcher_removal_inventory")
signatures_script = _script("butcher_signatures_3x")
INVENTORY = json.loads((DATA / "removal_inventory_3x.json").read_text(encoding="utf-8"))
SIGNATURES = json.loads((DATA / "signatures_3x.json").read_text(encoding="utf-8"))
# The files describe the 3.x surface and are generated on dev-3.x only; this checkout may add
# methods 3.x lacks. Each one is listed here, so a new one is a decision, not a silent gap.
NOT_IN_3X = {"Bot.stream"}  # D-05


def build_3x_signatures(build=signatures_script.build) -> dict:
    built = build()
    return {**built, "methods": {k: v for k, v in built["methods"].items() if k not in NOT_IN_3X}}


def crosscheck(records: list[dict], entries: list[dict]) -> list[str]:
    """Differences between the inventory and api-ledger entries (empty list = consistent).

    An entry covers the fields in ``fields`` of the entity named by the last component of
    ``warn_3x.target``; an entry with no ``fields`` covers the removed entity itself.
    """
    covered: dict[tuple[str, str | None], int] = {}
    for entry in entries:
        entity = entry["warn_3x"]["target"].rsplit(".", 1)[-1]
        for key in [(entity, f) for f in entry["fields"]] or [(entity, None)]:
            covered[key] = covered.get(key, 0) + 1
    wanted = {(r["entity"], r["field"]) for r in records}
    return (
        [f"{k}: listed {n} times" for k, n in covered.items() if n != 1]
        + [f"missing from api-ledger: {k}" for k in sorted(wanted - covered.keys(), key=str)]
        + [f"not in inventory: {k}" for k in sorted(covered.keys() - wanted, key=str)]
    )


def test_inventory_count_matches_entity_json_markers():
    fields = types = 0
    for path in (ROOT / ".butcher").glob("*/*/entity.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        types += "deprecated" in data.get("meta", {})
        fields += sum("deprecated" in a for a in data["object"].get("annotations", []))
    records = INVENTORY["records"]
    assert len([r for r in records if r["field"] is not None]) == fields
    assert len([r for r in records if r["field"] is None]) == types
    assert len({(r["entity"], r["field"]) for r in records}) == len(records)


def test_inventory_known_records():
    by_key = {(r["entity"], r["field"]): r for r in INVENTORY["records"]}
    assert by_key["SendMessage", "reply_to_message_id"]["replacement"] == "reply_parameters"
    assert by_key["Message", "forward_from"]["replacement"] == "forward_origin"
    assert by_key["Chat", "bio"]["replacement"] == "ChatFullInfo"
    assert by_key["UserShared", None]["replacement"] == "UsersShared"
    assert by_key["StoryAreaPosition", None]["replacement"] is None
    assert by_key["SendMessage", "receiver_user_id"]["replacement"] is None


def test_signatures_methods_and_shortcuts():
    assert SIGNATURES["methods"]["Bot.send_message"][:2] == ["chat_id", "text"]
    assert SIGNATURES["shortcuts"]["Message.answer"]["positional"][0] == "text"
    assert SIGNATURES["shortcuts"]["Message.answer"]["receiver"] == "Message"


def test_signatures_cover_everything():
    methods = SIGNATURES["methods"]
    for name, _ in inspect.getmembers(Bot, inspect.isfunction):
        assert name.startswith("_") or f"Bot.{name}" in methods or f"Bot.{name}" in NOT_IN_3X
    for cls in signatures_script._subclasses(TelegramMethod):
        assert cls.__name__ in methods
    for path in (ROOT / ".butcher" / "types").glob("*/aliases.yml"):
        for alias in re.findall(r"^([a-z_0-9]+):", path.read_text(encoding="utf-8"), re.M):
            assert f"{path.parent.name}.{alias}" in SIGNATURES["shortcuts"]


def test_collection_fields_and_observers():
    assert "entities" in SIGNATURES["collection_fields"]["Message"]
    assert SIGNATURES["observers"]["callback_query"] == "CallbackQuery"
    assert SIGNATURES["observers"]["error"] == "ErrorEvent"
    assert set(SIGNATURES["observers"]) == set(Router().observers)


def test_files_are_up_to_date_and_plain_json():
    assert inventory_script.build() == INVENTORY["records"]
    assert build_3x_signatures() == SIGNATURES
    assert NOT_IN_3X <= signatures_script.build()["methods"].keys()  # a stale entry fails here
    for name in ("removal_inventory_3x.json", "signatures_3x.json"):
        text = (DATA / name).read_text(encoding="utf-8")
        assert text == json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n"


def test_scripts_main(tmp_path, monkeypatch):
    for module, name in (
        (inventory_script, "removal_inventory_3x.json"),
        (signatures_script, "signatures_3x.json"),
    ):
        out = tmp_path / "x" / name
        monkeypatch.setattr(sys, "argv", ["script", "--out", str(out)])
        if module is signatures_script:
            monkeypatch.setattr(module, "build", build_3x_signatures)
        module.main()
        assert out.read_text(encoding="utf-8") == (DATA / name).read_text(encoding="utf-8")


def test_crosscheck_logic():
    records = [
        {"entity": "Chat", "field": "bio"},
        {"entity": "Chat", "field": "photo"},
        {"entity": "UserShared", "field": None},
    ]

    def entry(target, *fields):
        return {"fields": list(fields), "warn_3x": {"target": target}}

    ok = [entry("aiogram.types.Chat", "bio", "photo"), entry("aiogram.types.UserShared")]
    assert crosscheck(records, ok) == []
    assert len(crosscheck(records, ok[:1])) == 1
    assert len(crosscheck(records, [*ok, entry("aiogram.types.Chat", "bio")])) == 1
    assert len(crosscheck(records, [*ok, entry("aiogram.types.Chat", "nope")])) == 1


def test_inventory_covered_by_api_ledger():
    entries = [
        e
        for e in tomllib.loads(REGISTRY.read_text(encoding="utf-8"))["entry"]
        if e["kind"] == "api-ledger"
    ]
    if not entries:
        pytest.skip("no api-ledger entries yet; 3x-23 activates this check")
    assert crosscheck(INVENTORY["records"], entries) == []
