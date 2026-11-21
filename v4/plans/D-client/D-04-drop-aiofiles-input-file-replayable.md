# D-04 — Drop `aiofiles`; add `InputFile.replayable`

| Field | Value |
|---|---|
| Status | `done` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [D-05](D-05-download-lifecycle.md), [D-08](D-08-rust-encoder-multipart.md), [D-10](D-10-request-snapshot-and-render-hook.md), [D-16](D-16-cancellation-resource-tests.md), [G-13](../G-features/G-13-retry-middleware.md), [I-07](../I-distribution/I-07-dependencies-extras-restructure.md) |
| Gate-conditional | no |
| Decisions | D67, R19 |
| Sources | [08-build-release.md §8 D67](../../research/08-build-release.md), [19 §2 R19](../../research/19-review-resolutions.md), [05-network.md §2.5 D43](../../research/05-network.md), [codex-review.md R19](../../research/codex-review.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D67: `aiofiles` is dropped from core deps; path uploads and path downloads use chunked reads/writes in
`asyncio.to_thread`, the same thread-pool approach aiofiles uses internally. No API change.

R19: a retried upload must not silently resend a consumed stream. `InputFile.replayable` (True for built-ins) lets
`RetryMiddleware` (G-13) and the request snapshot (D-10) decide.

aiofiles uses today: `aiogram/types/input_file.py` (`FSInputFile.read`), `aiogram/client/bot.py`
(`Bot.__download_file`, `Bot.__aiofiles_reader`, module import), `pyproject.toml` (dependency + mypy/typing entry).

## Scope

**In:**
- `FSInputFile.read`: open, read chunks and close through `asyncio.to_thread`; the file handle is closed on normal
  end, `aclose()`, and cancellation (`try/finally` in the generator, close also via `to_thread`).
- `Bot` path download and local-mode reader (`api.is_local` branch in `download_file`): same helper. Put one small
  helper (e.g. `aiogram/utils/_fileio.py` with `iter_file(path, chunk_size)` and `write_stream(path, stream)`) used
  by both; no new dependency.
- `InputFile.replayable: bool` class attribute / property:
  - `BufferedInputFile`, `FSInputFile`, `URLInputFile` → `True` (re-reading produces the same bytes or re-fetches).
  - Base `InputFile` default → see Decide item.
- Remove `aiofiles` from `pyproject.toml` (dependency and any `types-aiofiles`/mypy overrides); `uv lock`.

**Out:**
- Download timeouts, `bot.stream()` → D-05.
- Retry policy using `replayable` → G-13; "consumed" tracking per request → D-10.
- Extras restructure → I-07 (this plan only removes aiofiles).

## Checklist

- [ ] File IO helper on `asyncio.to_thread`; `FSInputFile.read` and `Bot` download/local reader use it.
- [ ] Handle closed on early `aclose()` and on cancellation (test with a mocked open counting closes).
- [ ] `InputFile.replayable` on all built-ins.
- [ ] Decide the default `replayable` for user subclasses of `InputFile` (proposed default: `False`, so unknown
      custom streams are never retried; subclasses opt in) — record in Notes and flag to owner.
- [ ] Remove aiofiles from `pyproject.toml` and lockfile; `grep -r aiofiles aiogram tests` is empty.
- [ ] Tests (100% coverage of new code).
- [ ] Changelog fragments (`misc`: aiofiles dependency removed; `feature`: `replayable`). No migration-registry
      entry: no public API changes, and 3.x has no retries that the subclass default could alter.

## Acceptance criteria

- `import aiofiles` appears nowhere in `aiogram/`; the package installs without it.
- Uploading and downloading a 5 MB file by path produces identical bytes (sha256) to 3.x.
- Cancelling an upload mid-read leaves no open file descriptor (checked via `psutil`-free fd count or a patched
  `open`).
- `BufferedInputFile(...).replayable is FSInputFile(...).replayable is URLInputFile(...).replayable is True`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep aiofiles | Extra dependency for what `to_thread` does in a few lines | D67 |
| `anyio` file API | New dependency | D67, repo rule (no new deps) |
| Rewind arbitrary streams on retry | Not possible for generic async generators | R19 |

## Validation

```bash
uv lock
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Outputs: file IO helper (D-05), `replayable` (D-10, G-13).
- Parallel with D-01..D-03, D-06.

## Notes
