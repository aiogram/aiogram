"""
Verification for the sleep-scaling recipe in
``docs/dispatcher/testing.rst`` ("Speeding up the bot's own sleeps").

The code blocks are read out of the documentation itself, written
into a project of their own and run there, so the recipe cannot rot
without this failing.
"""

import re
import subprocess
import sys
import textwrap
from pathlib import Path

DOCS = Path(__file__).parents[2] / "docs" / "dispatcher" / "testing.rst"
HEADING = "Speeding up the bot's own sleeps"


def recipe_files():
    """Each code block of the recipe, keyed by its first-line path."""
    section = DOCS.read_text(encoding="utf-8").split(HEADING, 1)[1]
    section = re.split(r"\n\S[^\n]*\n=+\n", section, maxsplit=1)[0]
    blocks = re.findall(r"\.\. code-block:: python\n\n((?:    .*\n|\n)+)", section)
    files = {}
    for block in blocks:
        code = textwrap.dedent(block)
        path, _, body = code.partition("\n")
        files[path.removeprefix("# ")] = body
    return files


def test_the_recipe_names_its_files():
    assert sorted(recipe_files()) == [
        "game/clock.py",
        "game/engine.py",
        "tests/conftest.py",
        "tests/test_night.py",
    ]


def test_the_recipe_runs_and_keeps_the_loop_clock_real(tmp_path):
    for name, body in recipe_files().items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    (tmp_path / "game" / "__init__.py").write_text("", encoding="utf-8")
    # A second test, outside the recipe, that checks what it promises:
    # the loop's clock and asyncio.sleep stay real.
    (tmp_path / "tests" / "test_promise.py").write_text(
        textwrap.dedent(
            """
            import asyncio
            import time

            from game import clock


            async def test_only_the_game_clock_is_fast():
                assert clock.pause.__module__ == "conftest"
                assert asyncio.sleep.__module__ == "asyncio.tasks"
                loop = asyncio.get_running_loop()
                started, wall = loop.time(), time.monotonic()
                await asyncio.sleep(0.05)
                assert loop.time() - started >= 0.05
                assert time.monotonic() - wall >= 0.05
            """,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-q",
            "-p",
            "no:cacheprovider",
            "-o",
            "asyncio_mode=auto",
            "--durations=0",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "2 passed" in output
    # Fifteen virtual seconds took well under one real one.
    duration = re.search(r"([\d.]+)s call\s+tests/test_night.py", output)
    assert duration is not None, output
    assert float(duration.group(1)) < 1.0
