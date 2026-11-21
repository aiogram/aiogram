"""``python -m benchmarks run | compare | report`` (see benchmarks/README.md)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from benchmarks.harness import Settings, load_document
from benchmarks.runner import WORKTREE, compare, report, run


def duration(value: str) -> float:
    """``30`` / ``30s`` / ``5m`` -> seconds."""
    scale = {"s": 1, "m": 60, "h": 3600}.get(value[-1:])
    return float(value[:-1]) * scale if scale else float(value)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m benchmarks", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--cases", default="all", help="comma-separated A-04 ids, or 'all'")
    common.add_argument("--out", type=Path, help="write the result JSON here")
    common.add_argument("--gc-on", action="store_true", help="sustained GC-on mode")
    common.add_argument("--duration", type=duration, default=30.0, help="sustained: 30s, 5m, …")
    common.add_argument("--interval", type=duration, default=1.0, help="sustained: sample every")
    common.add_argument(
        "--loop", choices=["auto", "asyncio", "uvloop"], default="auto", help="auto: uvloop if any"
    )

    sub.add_parser("run", parents=[common], help="measure cases in this checkout")
    cmp = sub.add_parser("compare", parents=[common], help="A/B two git refs in one session")
    cmp.add_argument("--base", required=True, help="git ref")
    cmp.add_argument("--head", required=True, help=f"git ref, or {WORKTREE} for this checkout")
    rep = sub.add_parser("report", help="print one result file, or compare two")
    rep.add_argument("files", nargs="+", type=Path)

    args = parser.parse_args(argv)
    if args.command == "report":
        if len(args.files) > 2:  # noqa: PLR2004  one file, or a pair
            parser.error("report takes one or two files")
        report([load_document(f) for f in args.files], sys.stdout)
        return

    settings = Settings(
        gc=args.gc_on, duration_s=args.duration, interval_s=args.interval, loop=args.loop
    )
    if args.command == "run":
        doc = run(args.cases, settings, log=sys.stderr)
    else:
        doc = compare(args.base, args.head, args.cases, settings, log=sys.stderr)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    report([doc], sys.stdout)


if __name__ == "__main__":
    main()
