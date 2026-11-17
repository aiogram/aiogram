# D-16 — Cancellation and resource tests for uploads and downloads (D exit gate, part 2)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [D-03](D-03-token-safe-network-errors.md), [D-04](D-04-drop-aiofiles-input-file-replayable.md), [D-05](D-05-download-lifecycle.md), [D-08](D-08-rust-encoder-multipart.md), [D-11](D-11-session-on-new-codec.md) |
| Blocks | [J-01](../J-ga/J-01-feature-inventory-audit.md), [I-23](../I-distribution/I-23-beta-pre-release.md) |
| Gate-conditional | yes (upload half uses the Rust encoder; the download half could land earlier but ships with this PR) |
| Decisions | B9, D46, D67, R19 |
| Sources | [13-aiogram-rust-review.md §3 B9](../../research/13-aiogram-rust-review.md), [08-build-release.md §5](../../research/08-build-release.md), [05-network.md §2.5 D46](../../research/05-network.md), [README milestone D](../../research/README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

aiogram_rust's cancellation fuzz (4 boundaries × 8 seeds, 4 leak checks) caught a leak that reproduced on 8 of 8
seeds (13 B9). Milestone D's exit gate requires "cancellation/resource tests". Uploads now stream `InputFile.read()`
through `to_thread` file IO (D-04) and the new multipart path (D-08/D-11); downloads use `bot.stream()` (D-05).

## Scope

**In:**
- A local aiohttp test server (in `tests/`, no new dependency) with controllable delays at each boundary.
- Fuzz matrix: cancel at {before connect, mid request body (upload), awaiting response headers, mid response body
  (download)} × 8 deterministic seeds (seeded jitter of the cancel point), for: `sendDocument` with
  `FSInputFile`/`BufferedInputFile`/`URLInputFile`, `sendMediaGroup` with 2 files, `bot.download` to path and to
  `BytesIO`, `bot.stream` with early `break`.
- Leak checks after each case:
  1. no open file descriptors added (fd count via `/proc/self/fd` on Linux, `os.listdir('/dev/fd')` on macOS);
  2. aiohttp connector has no acquired connections;
  3. no un-finalised async generators (`sys.set_asyncgen_hooks` tracker) and no "Task was destroyed but it is
     pending";
  4. no pending tasks other than the test's own; no `to_thread` worker still holding a file.
- `session.close()` idempotent (twice, and after a cancelled request); `Bot` context manager closes the session.
- Token absence in every raised exception (D-03 helper).
- Run under `-W error::ResourceWarning`.

**Out:**
- Retry/rate-limit cancellation (token refunds) → G-13/G-14. Runner shutdown fault injection → E-21.

## Checklist

- [ ] Test server with boundary hooks.
- [ ] Fuzz matrix (4 × 8) for listed operations.
- [ ] Four leak checks as reusable helpers.
- [ ] `close()` idempotency tests.
- [ ] CI: runs on Linux and macOS; also on a free-threaded 3.14t job if I-03 provides one.
- [ ] Fix any leak found in the owning code (D-04/D-05/D-11 code paths) within this PR, or record it in Notes and
      block.

## Acceptance criteria

- All 4 × 8 × operations cases pass all four leak checks, deterministically (same seeds → same cancel points).
- A deliberately broken variant (generator without `finally`) is detected by the async-generator check (control).
- Suite runtime for the matrix ≤ 60 s on CI.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Random (unseeded) cancellation | Non-reproducible failures | B9 (seeded) |
| External fuzzing dependency (hypothesis etc.) | Avoid new deps for small tests | AGENTS.md maintainer signal |

## Validation

```bash
make dev
uv run pytest tests/test_api/test_client -W error::ResourceWarning
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: D-03 helper, D-04 IO, D-05 `bot.stream`, D-08/D-11 upload path.
- Can run in parallel with D-15. Together they close milestone D.

## Notes
