"""Self-tests of the request / response oracle (A-09): the canonicaliser, its comparators, the side."""

import ast
import datetime
import importlib.util
import json
import runpy
import sys
import tomllib
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent
if not (ROOT / "differential").is_dir():  # sdist: differential/ is not shipped
    pytest.skip("differential/ is not part of this checkout", allow_module_level=True)

from differential import runner, trace, wire  # noqa: E402
from differential.runner import Mismatch  # noqa: E402

SIDE = ROOT / "differential" / "sides" / "aiogram3" / "request.py"
CORPUS = ROOT / "benchmarks" / "corpus"
PNG = {"content_type": "image/png", "filename": "a.png"}


def multipart(*parts: tuple[str, str | None, bytes]) -> tuple[str, bytes]:
    body = b""
    for name, filename, payload in parts:
        disposition = f'form-data; name="{name}"' + (
            f'; filename="{filename}"' if filename else ""
        )
        content_type = "image/png" if filename else "text/plain; charset=utf-8"
        body += (
            (
                f"--B\r\nContent-Type: {content_type}\r\nContent-Disposition: {disposition}\r\n\r\n"
            ).encode()
            + payload
            + b"\r\n"
        )
    return "multipart/form-data; boundary=B", body + b"--B--\r\n"


def file_of(payload: bytes) -> dict:
    import hashlib

    return {"file": {**PNG, "sha256": hashlib.sha256(payload).hexdigest()}}


class TestCanonicalRequest:
    def test_module_is_stdlib_only(self):
        tree = ast.parse((ROOT / "differential" / "wire.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        assert imported <= sys.stdlib_module_names | {"__future__"}

    def test_urlencoded(self):
        body = b"chat_id=100&text=%D0%9F%D1%80%D0%B8&flag=true&markup=%7B%22a%22%3A1%7D&empty="
        resolved, encoding = wire.canonical_request("application/x-www-form-urlencoded", body)
        assert resolved == {
            "chat_id": 100,
            "text": "При",
            "flag": True,
            "markup": {"a": 1},
            "empty": "",
        }
        assert encoding == {
            "encoding": "urlencoded",
            "content_type": "application/x-www-form-urlencoded",
            "fields": ["chat_id", "text", "flag", "markup", "empty"],
        }

    def test_json_agrees_with_form(self):
        body = json.dumps({"chat_id": 100, "text": "hi", "markup": {"a": 1}, "id": "100"}).encode()
        resolved, encoding = wire.canonical_request("application/json; charset=utf-8", body)
        form, _ = wire.canonical_request(
            "application/x-www-form-urlencoded",
            b"chat_id=100&text=hi&markup=%7B%22a%22%3A1%7D&id=100",
        )
        assert resolved == form
        assert encoding == {
            "encoding": "json",
            "content_type": "application/json",
            "fields": ["chat_id", "text", "markup", "id"],
        }

    def test_empty_json_body(self):
        assert wire.canonical_request("application/json", b"") == (
            {},
            {"encoding": "json", "content_type": "application/json", "fields": []},
        )

    def test_multipart_attach_is_resolved(self):
        content_type, body = multipart(
            ("chat_id", None, b"1"),
            ("media", None, b'[{"type":"photo","media":"attach://k1"},{"media":"attach://k2"}]'),
            ("text", None, "Привіт\r\nдва".encode()),
            ("k1", "a.png", b"\x89PNG one"),
            ("k2", "a.png", b"\x89PNG two"),
        )
        resolved, encoding = wire.canonical_request(content_type, body)
        assert resolved == {
            "chat_id": 1,
            "media": [
                {"type": "photo", "media": file_of(b"\x89PNG one")},
                {"media": file_of(b"\x89PNG two")},
            ],
            "text": "Привіт\r\nдва",
        }
        assert encoding == {
            "encoding": "multipart",
            "content_type": "multipart/form-data",
            "fields": ["chat_id", "media", "text", "file#0", "file#1"],
        }

    def test_multipart_unreferenced_file_keeps_its_field(self):
        content_type, body = multipart(
            ("photo", "a.png", b"data"), ("caption", None, b"attach://missing")
        )
        resolved, _ = wire.canonical_request(content_type, body)
        assert resolved == {"photo": file_of(b"data"), "caption": "attach://missing"}

    def test_unsupported_content_type(self):
        with pytest.raises(ValueError, match="unsupported request content type"):
            wire.canonical_request("text/plain", b"x")


def record(value, *, ok=True, probe="encoding"):
    if ok:
        return trace.ok("request.x", probe, value)
    return trace.error("request.x", probe, RuntimeError("boom"))


FORM = {
    "encoding": "urlencoded",
    "content_type": "application/x-www-form-urlencoded",
    "fields": ["a"],
}
JSON = {"encoding": "json", "content_type": "application/json", "fields": ["a"]}
FILES = {"encoding": "multipart", "content_type": "multipart/form-data", "fields": ["a", "file#0"]}


class TestComparators:
    def judge(self, name, left, right):
        entry = runner.Entry(match="*", cls="approved", decision="X", assert_=name)
        return runner.compare([left], [right], [entry], {"aiogram3"}).mismatches

    def test_json_body_holds(self):
        assert self.judge("json_body_without_files", record(FORM), record(JSON)) == []

    def test_json_body_equal(self):
        assert self.judge("json_body_without_files", record(FILES), record(FILES)) == []

    @pytest.mark.parametrize(
        ("left", "right", "error"),
        [
            (record(FILES), record({**JSON, "fields": FILES["fields"]}), "must stay multipart"),
            (record(FORM), record({**FORM, "encoding": "multipart"}), "not a JSON body"),
            (record(FORM), record(None, ok=False), "both sides"),
        ],
    )
    def test_json_body_rejects(self, left, right, error):
        with pytest.raises(Mismatch, match=error):
            runner.COMPARATORS["json_body_without_files"](left, right)

    def test_json_body_rest_differs(self):
        (outcome,) = self.judge(
            "json_body_without_files", record(FORM), record({**JSON, "fields": ["b"]})
        )
        assert "the rest of the record differs" in outcome.reason

    def test_json_dumps_hook_holds(self):
        marked = {"a": 1, "m": [{runner.HOOK_MARK: True, "b": 2}]}
        left, right = (
            record(marked, probe="resolved"),
            record({"a": 1, "m": [{"b": 2}]}, probe="resolved"),
        )
        assert self.judge("json_dumps_hook_ignored", left, right) == []

    @pytest.mark.parametrize(
        ("left", "right"),
        [
            ({"a": 1}, {"a": 1}),  # no mark on the left: the hook did not run
            ({"a": 1, runner.HOOK_MARK: True}, {"a": 2}),  # more than the mark differs
        ],
    )
    def test_json_dumps_hook_rejects(self, left, right):
        with pytest.raises(Mismatch, match="without the custom json_dumps mark"):
            runner.COMPARATORS["json_dumps_hook_ignored"](record(left), record(right))


def load_side() -> ModuleType:
    spec = importlib.util.spec_from_file_location("differential_request_side", SIDE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestSide:
    def run(self, tmp_path, monkeypatch, *, poison):
        out = tmp_path / f"{poison}.jsonl"
        argv = [
            "request.py",
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

    def test_in_process(self, tmp_path, monkeypatch):
        """The aiogram3 request side against this checkout, run in-process (no venv)."""
        clean = self.run(tmp_path, monkeypatch, poison=False)
        poisoned = self.run(tmp_path, monkeypatch, poison=True)
        assert clean[0]["adapter"] == "aiogram3"
        keys = {f"{r['case']}/{r['probe']}": r for r in clean[1]}
        manifest = tomllib.loads((CORPUS / "MANIFEST.toml").read_text(encoding="utf-8"))
        for item in manifest["input"]:
            probes = {"request": ("resolved", "encoding", "serialize"), "response": ("decode",)}
            for probe in probes.get(item["kind"], ()):
                assert f"{item['id']}/{probe}" in keys
            if item["kind"] == "response":
                outcome = keys[f"{item['id']}/decode"]
                assert (outcome["ok"] and item["on_3x"] == "ok") or (
                    outcome["error"]["type"] == item["on_3x"]
                )
        assert all(record["ok"] for key, record in keys.items() if not key.startswith("response."))
        assert keys["request.datetime.timedelta/resolved"]["value"]["until_date"] == {
            "now_plus": 86400
        }
        assert keys["request.hooks.json_dumps/resolved"]["value"]["reply_markup"][runner.HOOK_MARK]
        assert (
            keys["webhook.reply.photo/resolved"]["value"]["photo"]["file"]["filename"] == "red.png"
        )
        assert keys["request.sendPhoto.upload/serialize"]["value"]["files"] == {
            "file#0": "red.png"
        }
        entries = runner.load_manifest(ROOT / "differential" / "manifests" / "request.toml")
        assert runner.evaluate(clean, clean, entries, poison=None)[0] == runner.EXIT_OK
        assert runner.evaluate(clean, poisoned, entries, poison="right")[0] == runner.EXIT_MISMATCH

    def test_timedelta_outside_the_window_keeps_the_offset(self):
        side = load_side()
        instance = side.Side(trace, wire, CORPUS, poison=False)
        delta = datetime.timedelta(seconds=60)
        instance.wire_records(
            "c",
            "application/x-www-form-urlencoded",
            b"until_date=1100",
            {},
            {"until_date": delta},
            (1000.0, 1001.0),
        )
        assert instance.records[0]["value"] == {"until_date": {"now_plus": 40}}

    def test_failed_send_is_recorded(self):
        side = load_side()

        async def go():
            instance = side.Side(trace, wire, CORPUS, poison=False)
            async with instance.api.server:
                await instance.send(
                    "c", side.methods.GetMe(), session=instance.api.session(Broken)
                )
            return instance.records

        class Broken(side.AiohttpSession):
            def build_form_data(self, bot, method):
                raise RuntimeError("broken")

        import asyncio

        records = asyncio.run(go())
        assert [(r["probe"], r["ok"], r["error"]["type"]) for r in records] == [
            ("resolved", False, "RuntimeError"),
            ("encoding", False, "RuntimeError"),
        ]
