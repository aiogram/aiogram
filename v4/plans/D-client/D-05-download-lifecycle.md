# D-05 — Download lifecycle: per-phase timeouts, `bot.stream()`, typed overloads

| Field | Value |
|---|---|
| Status | `done` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [D-03](D-03-token-safe-network-errors.md), [D-04](D-04-drop-aiofiles-input-file-replayable.md) |
| Blocks | [D-16](D-16-cancellation-resource-tests.md) |
| Gate-conditional | no |
| Decisions | D46, D45 |
| Sources | [05-network.md §2.5 D46](../../research/05-network.md), [13-aiogram-rust-review.md §3 B9](../../research/13-aiogram-rust-review.md), [19](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

3.x downloads (`Bot.download`, `Bot.download_file` in `aiogram/client/bot.py`; `AiohttpSession.stream_content`)
use one `ClientTimeout(total=30)`: large files on slow links fail, and stalled connections are only caught by the
total cap. There is no streaming API for consumers, and the stream is not closed on every path (D46 notes a
traceback leak; the related evidence is aiogram_rust's cancellation fuzz, 13 §3 B9 — 05 cites "13 §4" by mistake).

D46: per-phase timeouts (`connect`, `sock_read` idle), no total cap by default, optional `total=`; new
`async for chunk in bot.stream(file_or_path, chunk_size=…)`; typed overloads; old kwargs accepted, an int `timeout=`
maps to `total=`; the stream is closed on every path.

## Scope

**In:**
- A small public timeout value, e.g. `aiogram.client.session.base.DownloadTimeout(connect: float | None = 30,
  sock_read: float | None = 30, total: float | None = None)` (frozen dataclass). Exact defaults: see Decide item.
- `BaseSession.stream_content(url, headers=None, timeout=…, chunk_size=65536, raise_for_status=True)`: `timeout`
  accepts `DownloadTimeout | int | float`; int/float → `DownloadTimeout(total=value)` (compat).
- `AiohttpSession.stream_content` → `ClientTimeout(connect=…, sock_read=…, total=…)`; errors wrapped by D-03.
- `Bot.stream(file: str | Downloadable, *, chunk_size=65536, timeout=…) -> AsyncIterator[bytes]` — resolves
  `file_id` via `get_file` like `Bot.download`, supports local mode (`session.api.is_local`, D-04 helper). The
  returned iterator is an async context manager too, and is closed on normal end, `break` + `aclose()`, exception and
  cancellation.
- `Bot.download` / `Bot.download_file` reimplemented on `Bot.stream`, with `typing.overload`s:
  destination `str | Path` → `None`; `BinaryIO | None` → `BinaryIO`. `seek` kept.
- Custom sessions overriding the old `stream_content` signature keep working (Decide item).

**Out:**
- Token-safe errors → D-03 (dependency). Cancellation fuzz → D-16.
- Request (non-download) timeouts: unchanged (`session.timeout`, `request_timeout`).
- `URLInputFile` timeout semantics: unchanged except that its `int` `timeout` now flows as `total` through the shim.

## Checklist

- [ ] `DownloadTimeout` type + int/float compat mapping.
- [ ] Decide `DownloadTimeout` defaults (proposed default: `connect=30`, `sock_read=60`, `total=None`) — record in
      Notes and flag to owner.
- [ ] Decide the `stream_content` compatibility shim for custom sessions whose override still takes `timeout: int`
      (proposed default: `BaseSession` checks once per subclass whether the override is `AiohttpSession`'s/the
      base's; for third-party overrides it passes `int(total)` when `total` is set, otherwise the legacy `30`, and
      emits one `AiogramDeprecationWarning` per class) — record in Notes and flag to owner.
- [ ] `AiohttpSession.stream_content` per-phase `ClientTimeout`.
- [ ] `Bot.stream()` with close-on-every-path; `download`/`download_file` on top of it; overloads.
- [ ] `assert_type` checks for the overloads in the typing test suite.
- [ ] Docs: downloads page (per-phase timeouts, `bot.stream()`, overload return types).
- [ ] Tests (100% coverage of new code), incl. slow-trickle server (no total cap → completes), stalled server
      (sock_read fires), early `break`.
- [ ] Migration-registry entry (PD-13): default download timeout changes from total 30 s to per-phase.
- [ ] Changelog fragments: `feature` (`bot.stream`, timeouts), `removal`/behaviour note (default timeout).

## Acceptance criteria

- A local aiohttp test server that sends 1 byte every 1 s for 45 s completes with defaults; a server that stalls for
  `sock_read + 1` s raises `TelegramNetworkError` without the token in any text (D-03 helper).
- `download(..., timeout=5)` behaves as `total=5`.
- After `async for chunk in bot.stream(...): break`, the underlying response is released (aiohttp connector has
  no acquired connections) and no `ResourceWarning`/"Task was destroyed" is emitted under `-W error`.
- `reveal_type(await bot.download(f, "x.bin"))` is `None`; with `io.BytesIO()` it is `BinaryIO`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep a single total timeout | Fails large files, misses stalls | D46 |
| Rust HTTP client for downloads | No Rust networking (tokio bridge, fork safety) | D5, 05 §3 |
| Break `stream_content` signature without a shim | Custom sessions must keep working (05 §2.3) | 05 §2.3 |

## Validation

```bash
make dev
uv run pytest tests/test_api/test_client
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: D-03 (error wrapping, token helper), D-04 (to_thread file IO).
- Outputs: `Bot.stream` and close-on-every-path behaviour exercised by D-16.

## Notes
