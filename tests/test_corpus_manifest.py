"""Integrity of the pinned corpus in benchmarks/corpus (A-04)."""

import hashlib
import json
import re
import tomllib
from pathlib import Path

import pytest

from aiogram import methods
from aiogram.types import Update

CORPUS = Path(__file__).parent.parent / "benchmarks" / "corpus"
if not (CORPUS / "MANIFEST.toml").exists():
    pytest.skip("benchmarks/ is not part of this tree (sdist)", allow_module_level=True)

MANIFEST = tomllib.loads((CORPUS / "MANIFEST.toml").read_text(encoding="utf-8"))
INPUTS = MANIFEST["input"]
BY_ID = {entry["id"]: entry for entry in INPUTS}
DOCS = {"MANIFEST.toml", "README.md"}
TOKEN_RE = re.compile(rb"\d{5,}:[A-Za-z0-9_-]{30,}")
KINDS = {
    "update",
    "response",
    "routing",
    "request",
    "file",
    "keyboard",
    "entities",
    "callback_data",
    "trace",
    "case",
}


def corpus_files() -> set[str]:
    return {p.relative_to(CORPUS).as_posix() for p in CORPUS.rglob("*") if p.is_file()}


def test_ids_are_unique():
    assert len(BY_ID) == len(INPUTS)


@pytest.mark.parametrize("entry", INPUTS, ids=lambda entry: entry["id"])
def test_entry(entry):
    assert entry["kind"] in KINDS
    provenance = entry["provenance"]
    assert provenance["source"] in {"hand", "recorded", "synthesised"}
    assert {"date", "aiogram", "bot_api", "author"} <= provenance.keys()

    if entry["kind"] == "case":
        assert "path" not in entry
        assert "sha256" not in entry
        assert all(uses in BY_ID for uses in entry.get("uses", []))
        return

    path = CORPUS / entry["path"]
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]


def test_every_file_is_listed():
    listed = {entry["path"] for entry in INPUTS if "path" in entry}
    assert corpus_files() - DOCS == listed


def test_no_token_in_corpus():
    for name in corpus_files():
        assert not TOKEN_RE.search((CORPUS / name).read_bytes()), name


def test_references_resolve():
    for entry in INPUTS:
        if entry["kind"] == "routing":
            topology = tomllib.loads((CORPUS / entry["path"]).read_text(encoding="utf-8"))
            for event in topology["event"]:
                assert BY_ID[event["update"]]["kind"] == "update", event
        elif entry["kind"] == "request":
            text = (CORPUS / entry["path"]).read_text(encoding="utf-8")
            for name in re.findall(r'corpus_file = "([^"]+)"', text):
                assert f"files/{name}" in {e.get("path") for e in INPUTS}, name


def test_traces_are_redacted():
    for entry in INPUTS:
        if entry["kind"] == "trace":
            assert entry["provenance"]["source"] == "recorded"
            first = (CORPUS / entry["path"]).read_text(encoding="utf-8").splitlines()[0]
            assert json.loads(first)["provenance"]["redacted"]


@pytest.mark.parametrize(
    "entry",
    [entry for entry in INPUTS if "on_3x" in entry],
    ids=lambda entry: entry["id"],
)
def test_on_3x(entry, bot):
    content = (CORPUS / entry["path"]).read_text(encoding="utf-8")
    try:
        if entry["kind"] == "update":
            Update.model_validate_json(content, context={"bot": bot}).event_type  # noqa: B018
        else:
            name = entry["method"]
            method = getattr(methods, name[0].upper() + name[1:]).model_construct()
            bot.session.check_response(bot, method, entry["status"], content)
    except Exception as e:  # noqa: BLE001
        outcome = type(e).__name__
    else:
        outcome = "ok"
    assert outcome == entry["on_3x"]
