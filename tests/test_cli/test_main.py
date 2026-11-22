import argparse
import io
import json
import os
import subprocess
import sys
import tomllib
import types
from importlib import metadata
from pathlib import Path

import pytest

import aiogram
from aiogram.cli import CliError, _info, _migrate, _output, _plugins, _token, main
from aiogram.cli._spec import add_token_arguments, build_parser
from tests.token_safety import FAKE_TOKEN

ROOT = Path(aiogram.__file__).parent
INFO_KEYS = {
    "aiogram",
    "core",
    "python",
    "implementation",
    "free_threaded",
    "gil_enabled",
    "wheel_tag",
    "installed_optional_packages",
}


def run_python(*args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "NO_COLOR": "1"}
    return subprocess.run(
        [sys.executable, *args], capture_output=True, text=True, check=False, env=env
    )


class TestEntryPoints:
    def test_console_script_is_declared(self):
        with (ROOT.parent / "pyproject.toml").open("rb") as f:
            scripts = tomllib.load(f)["project"]["scripts"]
        assert scripts == {"aiogram": "aiogram.cli:main"}

    def test_module_and_script_print_the_same_help(self):
        # CI tests the checkout without installing the project (no console script), so the
        # script side runs `main` the way the generated wrapper does: argv[0] is its path
        by_module = run_python("-m", "aiogram", "--help")
        by_script = run_python(
            "-c",
            "import sys; sys.argv[0] = '/venv/bin/aiogram'; "
            "from aiogram.cli import main; sys.exit(main())",
            "--help",
        )
        assert by_module.returncode == by_script.returncode == 0
        assert by_module.stdout == by_script.stdout
        assert by_module.stdout.startswith("usage: aiogram ")

    def test_main_module_without_command(self):
        result = run_python("-m", "aiogram")
        assert result.returncode == 2
        assert "required: <command>" in result.stderr

    def test_import_aiogram_does_not_load_the_cli(self):
        result = run_python(
            "-c",
            "import sys, aiogram; "
            "print([m for m in sys.modules if m == 'aiogram.cli' or m.startswith('aiogram.cli.')])",
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "[]"

    def test_spec_builds_without_aiogram(self):
        code = (
            "import importlib.util, sys\n"
            "spec = importlib.util.spec_from_file_location('cli_spec', sys.argv[1])\n"
            "module = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(module)\n"
            "parser, subparsers = module.build_parser()\n"
            "assert sorted(subparsers.choices) == ['info', 'migrate'], subparsers.choices\n"
            "parser.format_help()\n"
            "assert not [m for m in sys.modules if m.startswith('aiogram')], sys.modules\n"
        )
        result = run_python("-I", "-c", code, str(ROOT / "cli" / "_spec.py"))
        assert result.returncode == 0, result.stderr


class TestMain:
    def test_help(self, capsys: pytest.CaptureFixture[str]):
        assert main(["--help"]) == 0
        assert "info" in capsys.readouterr().out

    def test_version(self, capsys: pytest.CaptureFixture[str]):
        assert main(["--version"]) == 0
        assert capsys.readouterr().out.strip() == f"aiogram {aiogram.__version__}"

    @pytest.mark.parametrize("argv", [["nosuch"], [], ["info", "--nosuch"]])
    def test_usage_error(self, argv: list[str]):
        assert main(argv) == 2

    def test_non_int_system_exit(self, monkeypatch: pytest.MonkeyPatch):
        def parse_args(self, args=None, namespace=None):
            raise SystemExit("message")

        monkeypatch.setattr(argparse.ArgumentParser, "parse_args", parse_args)
        assert main(["info"]) == 1


def fake_entry_point(name: str, target, dist: str | None = "fake-dist"):
    module = types.ModuleType(f"fake_plugin_{name}")
    module.register = target
    sys.modules[module.__name__] = module
    entry_point = metadata.EntryPoint(name, f"{module.__name__}:register", _plugins.GROUP)
    distribution = None if dist is None else types.SimpleNamespace(name=dist)
    return types.SimpleNamespace(name=name, load=entry_point.load, dist=distribution)


@pytest.fixture
def plugins(monkeypatch: pytest.MonkeyPatch):
    found: list = []

    def entry_points(group: str):
        assert group == "aiogram.cli"
        return list(found)

    monkeypatch.setattr(_plugins, "entry_points", entry_points)
    yield found
    for entry_point in found:
        sys.modules.pop(f"fake_plugin_{entry_point.name}", None)


def command(name: str, handler, aliases: tuple[str, ...] = ()):
    def register(subparsers):
        parser = subparsers.add_parser(name, help=f"{name} command", aliases=list(aliases))
        parser.add_argument("--value", default="x")
        parser.set_defaults(func=handler)

    return register


class TestPlugins:
    def test_plugin_command_runs(self, plugins, capsys: pytest.CaptureFixture[str]):
        plugins.append(fake_entry_point("hello", command("hello", lambda a: print(a.value))))
        assert main(["hello", "--value", "world"]) == 0
        assert capsys.readouterr().out == "world\n"

    def test_handler_exit_code(self, plugins):
        plugins.append(fake_entry_point("hello", command("hello", lambda a: 5)))
        assert main(["hello"]) == 5

    def test_guard_forwards_attributes(self, plugins):
        seen = []
        plugins.append(fake_entry_point("peek", lambda sub: seen.append(sorted(sub.choices))))
        assert main(["info", "--json"]) == 0
        assert seen == [["info", "migrate"]]

    def test_broken_import_is_reported(self, plugins, capsys: pytest.CaptureFixture[str]):
        def broken():
            raise ImportError("no module named nowhere")

        plugins.append(types.SimpleNamespace(name="broken", load=broken, dist=None))
        assert main(["info", "--json"]) == 0
        captured = capsys.readouterr()
        assert set(json.loads(captured.out)) == INFO_KEYS
        assert captured.err == (
            "aiogram: warning: plugin 'broken' (unknown distribution) failed to load: "
            "ImportError: no module named nowhere\n"
        )

    def test_broken_register_is_reported(self, plugins, capsys: pytest.CaptureFixture[str]):
        def register(subparsers):
            raise RuntimeError("boom")

        plugins.append(fake_entry_point("bad", register))
        plugins.append(fake_entry_point("good", command("good", lambda a: 0)))
        assert main(["good"]) == 0
        assert (
            "plugin 'bad' (fake-dist) failed to load: RuntimeError: boom"
            in capsys.readouterr().err
        )

    def test_partial_register_is_rolled_back(self, plugins, capsys: pytest.CaptureFixture[str]):
        def register(subparsers):
            subparsers.add_parser("half", aliases=["h"], help="broken half")
            raise RuntimeError("boom")

        plugins.append(fake_entry_point("bad", register))
        plugins.append(fake_entry_point("good", command("half", lambda a: 7)))
        assert main(["half"]) == 7
        assert main(["h"]) == 2
        assert main(["--help"]) == 0
        out = capsys.readouterr().out
        assert "broken half" not in out
        assert "half command" in out

    def test_system_exit_in_plugin(self, plugins, capsys: pytest.CaptureFixture[str]):
        def register(subparsers):
            raise SystemExit("missing config")

        plugins.append(fake_entry_point("bad", register))
        assert main(["info", "--json"]) == 0
        assert "failed to load: SystemExit: missing config" in capsys.readouterr().err

    def test_plugin_warning_is_redacted(self, plugins, capsys: pytest.CaptureFixture[str]):
        def register(subparsers):
            raise RuntimeError(f"bad token {FAKE_TOKEN}")

        plugins.append(fake_entry_point("bad", register))
        assert main(["info", "--json"]) == 0
        err = capsys.readouterr().err
        assert FAKE_TOKEN.partition(":")[2] not in err
        assert "123456:***" in err

    def test_builtin_wins(self, plugins, capsys: pytest.CaptureFixture[str]):
        plugins.append(fake_entry_point("info", command("info", lambda a: 9), dist="evil"))
        assert main(["info", "--json"]) == 0
        assert capsys.readouterr().err.splitlines() == [
            "aiogram: warning: command 'info' of plugin 'info' (evil) is ignored: "
            "aiogram (built-in) provides it"
        ]

    def test_first_plugin_by_name_wins(self, plugins, capsys: pytest.CaptureFixture[str]):
        # registered out of order: loading sorts by entry-point name, so "a" wins
        plugins.append(fake_entry_point("b", command("hello", lambda a: 2), dist="dist-b"))
        plugins.append(fake_entry_point("a", command("hello", lambda a: 1), dist="dist-a"))
        assert main(["hello"]) == 1
        assert capsys.readouterr().err.splitlines() == [
            "aiogram: warning: command 'hello' of plugin 'b' (dist-b) is ignored: "
            "plugin 'a' (dist-a) provides it"
        ]

    def test_alias_collision_keeps_the_command(self, plugins, capsys: pytest.CaptureFixture[str]):
        plugins.append(
            fake_entry_point("p", command("doctor", lambda a: 4, aliases=("info", "doc")))
        )
        assert main(["doc"]) == 4
        assert main(["doctor"]) == 4
        assert main(["info", "--json"]) == 0
        assert "command 'info' of plugin 'p' (fake-dist) is ignored" in capsys.readouterr().err

    def test_command_without_handler(self, plugins, capsys: pytest.CaptureFixture[str]):
        plugins.append(fake_entry_point("p", lambda sub: sub.add_parser("bare")))
        assert main(["bare"]) == 1
        assert capsys.readouterr().err == "aiogram: error: this command has no handler\n"


class TestErrors:
    def test_cli_error(self, plugins, capsys: pytest.CaptureFixture[str]):
        def handler(args):
            raise CliError("bad input", exit_code=2)

        plugins.append(fake_entry_point("p", command("p", handler)))
        assert main(["p"]) == 2
        assert capsys.readouterr().err == "aiogram: error: bad input\n"

    def test_unexpected_error(self, plugins, capsys: pytest.CaptureFixture[str]):
        def handler(args):
            raise ValueError("oops")

        plugins.append(fake_entry_point("p", command("p", handler)))
        assert main(["p"]) == 1
        assert capsys.readouterr().err == "aiogram: error: ValueError: oops\n"

    def test_traceback(self, plugins, capsys: pytest.CaptureFixture[str]):
        def handler(args):
            raise ValueError("oops")

        plugins.append(fake_entry_point("p", command("p", handler)))
        assert main(["--traceback", "p"]) == 1
        err = capsys.readouterr().err
        assert "Traceback (most recent call last)" in err
        assert err.endswith("aiogram: error: ValueError: oops\n")

    def test_token_is_redacted(
        self, plugins, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ):
        monkeypatch.setattr(_output, "_hidden", set())
        monkeypatch.setenv("BOT_TOKEN", FAKE_TOKEN)

        def register(subparsers):
            parser = subparsers.add_parser("leak")
            add_token_arguments(parser)
            parser.set_defaults(func=handler)

        def handler(args):
            token = _token.resolve_token(args)
            raise RuntimeError(f"request to /bot{token}/getMe failed")

        plugins.append(fake_entry_point("p", register))
        assert main(["--traceback", "leak"]) == 1
        err = capsys.readouterr().err
        assert FAKE_TOKEN.partition(":")[2] not in err
        assert f"/bot{FAKE_TOKEN.partition(':')[0]}:***/getMe" in err


class TestUsageErrorRedaction:
    @pytest.mark.parametrize(
        "argv",
        [
            ["info", "--token", FAKE_TOKEN],
            ["info", f"--token={FAKE_TOKEN}"],
            [FAKE_TOKEN],
        ],
    )
    def test_token_in_usage_error(self, argv: list[str], capsys: pytest.CaptureFixture[str]):
        assert main(argv) == 2
        err = capsys.readouterr().err
        assert "error:" in err
        assert FAKE_TOKEN.partition(":")[2] not in err
        assert "123456:***" in err


class TestToken:
    @pytest.fixture(autouse=True)
    def clean(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(_output, "_hidden", set())
        monkeypatch.delenv("BOT_TOKEN", raising=False)

    def parse(self, *argv: str) -> argparse.Namespace:
        parser = argparse.ArgumentParser()
        add_token_arguments(parser)
        return parser.parse_args(argv)

    def test_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("BOT_TOKEN", f" {FAKE_TOKEN}\n")
        assert _token.resolve_token(self.parse()) == FAKE_TOKEN

    def test_file_beats_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("BOT_TOKEN", "1:env")
        path = tmp_path / "token"
        path.write_text(f"{FAKE_TOKEN}\n", encoding="utf-8")
        assert _token.resolve_token(self.parse("--token-file", str(path))) == FAKE_TOKEN

    def test_missing_file(self, tmp_path: Path):
        with pytest.raises(CliError, match="cannot read --token-file") as exc:
            _token.resolve_token(self.parse("--token-file", str(tmp_path / "nope")))
        assert exc.value.exit_code == 2

    def test_undecodable_file(self, tmp_path: Path):
        path = tmp_path / "token"
        path.write_bytes(b"\xff\xfe")
        with pytest.raises(CliError, match="cannot read --token-file") as exc:
            _token.resolve_token(self.parse("--token-file", str(path)))
        assert exc.value.exit_code == 2

    def test_flag_warns(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
        monkeypatch.setenv("BOT_TOKEN", "1:env")
        assert _token.resolve_token(self.parse("--token", FAKE_TOKEN)) == FAKE_TOKEN
        err = capsys.readouterr().err
        assert "--token ends up in shell history" in err
        assert FAKE_TOKEN.partition(":")[2] not in err

    def test_flag_and_file_exclusive(self):
        with pytest.raises(SystemExit):
            self.parse("--token", "1:a", "--token-file", "x")

    @pytest.mark.parametrize("value", [None, "", "  "])
    def test_missing(self, value: str | None, monkeypatch: pytest.MonkeyPatch):
        if value is not None:
            monkeypatch.setenv("BOT_TOKEN", value)
        with pytest.raises(CliError, match=r"no bot token") as exc:
            _token.resolve_token(self.parse())
        assert exc.value.exit_code == 2

    def test_redact_without_colon(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("BOT_TOKEN", "opaque")
        _token.resolve_token(self.parse())
        assert _output.redact("x opaque y") == "x *** y"


class TTY(io.StringIO):
    def isatty(self) -> bool:
        return True


class TestColour:
    def test_tty(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("NO_COLOR", raising=False)
        assert _output.paint("x", "red", TTY()) == "\033[31mx\033[0m"

    def test_no_color(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("NO_COLOR", "1")
        assert _output.paint("x", "red", TTY()) == "x"

    def test_empty_no_color_is_unset(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("NO_COLOR", "")
        assert _output.paint("x", "red", TTY()) != "x"

    def test_not_a_tty(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("NO_COLOR", raising=False)
        assert _output.paint("x", "red", io.StringIO()) == "x"

    def test_warning_on_tty(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("NO_COLOR", raising=False)
        stream = TTY()
        monkeypatch.setattr(sys, "stderr", stream)
        _output.warn("w")
        assert stream.getvalue() == "aiogram: \033[33mwarning\033[0m: w\n"


class TestInfo:
    def test_json(self, capsys: pytest.CaptureFixture[str]):
        assert main(["info", "--json"]) == 0
        data = json.loads(capsys.readouterr().out)
        assert set(data) == INFO_KEYS
        assert data["aiogram"] == aiogram.__version__
        assert set(data["core"]) >= {"version", "profile", "target"}
        assert data["implementation"] == sys.implementation.name
        assert isinstance(data["free_threaded"], bool)
        assert isinstance(data["gil_enabled"], bool)
        assert all(isinstance(v, str) for v in data["installed_optional_packages"].values())

    def test_text(self, capsys: pytest.CaptureFixture[str]):
        assert main(["info"]) == 0
        out = capsys.readouterr().out
        assert f"aiogram: {aiogram.__version__}\n" in out
        assert "rust core: " in out
        assert "installed optional packages:\n" in out

    def test_core_missing(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ):
        monkeypatch.setitem(sys.modules, "aiogram._core", None)
        assert main(["info"]) == 0
        assert "rust core: not loaded (ModuleNotFoundError: " in capsys.readouterr().out
        data, error = _info.collect()
        assert data["core"] is None
        assert error is not None

    def test_not_installed(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ):
        def distribution(name: str):
            raise metadata.PackageNotFoundError(name)

        monkeypatch.setattr(_info.metadata, "distribution", distribution)
        assert main(["info"]) == 0
        out = capsys.readouterr().out
        assert "wheel tag: unknown\n" in out
        assert out.endswith("installed optional packages:\n  (none)\n")

    def test_without_is_gil_enabled(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delattr(sys, "_is_gil_enabled", raising=False)
        assert _info.collect()[0]["gil_enabled"] is True

    def test_metadata_parsing(self, monkeypatch: pytest.MonkeyPatch):
        dist = types.SimpleNamespace(
            requires=[
                "aiohttp>=3.9",
                "redis[hiredis]>=6.2.0,<8 ; extra == 'redis'",
                "Some_Package.Name>=1 ; extra == 'x'",
                "missing-package ; extra == 'y'",
            ],
            read_text=lambda name: "Wheel-Version: 1.0\nTag: py3-none-any\nTag: cp311-abi3-any\n",
        )
        versions = {"redis": "7.0", "some-package-name": "1.2"}

        def version(name: str) -> str:
            if name not in versions:
                raise metadata.PackageNotFoundError(name)
            return versions[name]

        monkeypatch.setattr(_info.metadata, "version", version)
        assert _info._optional_packages(dist) == {"redis": "7.0", "some-package-name": "1.2"}
        assert _info._wheel_tag(dist) == "py3-none-any, cp311-abi3-any"
        dist.requires = None
        dist.read_text = lambda name: None
        assert _info._optional_packages(dist) == {}
        assert _info._wheel_tag(dist) is None


class TestMigrate:
    def test_not_available(self, capsys: pytest.CaptureFixture[str]):
        assert main(["migrate", "check", "src"]) == 2
        assert (
            capsys.readouterr().err
            == "aiogram: error: aiogram migrate is not available in this build\n"
        )

    def test_paths_required(self):
        assert main(["migrate", "check"]) == 2
        assert main(["migrate"]) == 2

    def test_without_libcst(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ):
        def import_module(name: str):
            assert name == "aiogram.migrate"
            raise ModuleNotFoundError("No module named 'libcst'", name="libcst")

        monkeypatch.setattr(
            _migrate, "importlib", types.SimpleNamespace(import_module=import_module)
        )
        assert main(["migrate", "fix", "src"]) == 2
        assert "pip install 'aiogram[migrate]'" in capsys.readouterr().err

    def test_other_missing_module_propagates(self, monkeypatch: pytest.MonkeyPatch):
        def import_module(name: str):
            raise ModuleNotFoundError("No module named 'other'", name="other")

        monkeypatch.setattr(
            _migrate, "importlib", types.SimpleNamespace(import_module=import_module)
        )
        assert main(["migrate", "fix", "src"]) == 1

    def test_engine(self, monkeypatch: pytest.MonkeyPatch):
        calls = []
        engine = types.ModuleType("aiogram.migrate")
        engine.run = lambda args: calls.append((args.migrate_command, args.paths)) or 3
        monkeypatch.setitem(sys.modules, "aiogram.migrate", engine)
        assert main(["migrate", "check", "a", "b"]) == 3
        assert calls == [("check", ["a", "b"])]


def test_build_parser_default_version(capsys: pytest.CaptureFixture[str]):
    parser, _ = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--version"])
    assert capsys.readouterr().out == "aiogram unknown\n"
