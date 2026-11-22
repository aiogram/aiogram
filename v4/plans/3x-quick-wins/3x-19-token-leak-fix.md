# 3x-19 — Stop leaking the bot token through network/download errors (ANT-2026-4GL80S7S)

| Field | Value |
|---|---|
| Status | `done` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | — |
| Blocks | — |
| Gate-conditional | no |
| Decisions | PD-14 (3.x shape), R22, D66 |
| Sources | [19 header + R22](../../research/19-review-resolutions.md), [15 §5](../../research/15-observability.md), [codex-review R22, §11](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

aiohttp exceptions render the request URL, and the URL contains the token (`/bot<token>/…`, `/file/bot<token>/…`).
3.x leaks it in two places:
- `AiohttpSession.make_request` (`aiogram/client/session/aiohttp.py`) raises
  `TelegramNetworkError(message=f"{type(e).__name__}: {e}") from e`. The message can contain the URL, and the
  chained `__cause__` is printed in every formatted traceback even when the message is clean (codex §11 probe).
- `AiohttpSession.stream_content`, used by `Bot.download_file` / `Bot.download` (`aiogram/client/bot.py`), lets a
  raw `aiohttp.ClientResponseError` escape (`raise_for_status=True`), and its text contains `/file/bot<token>/`.

This is OSS Scanner finding **ANT-2026-4GL80S7S** (medium) and a security patch.

[3x-01](3x-01-polling-poison-isolation.md) touches the same client code. The fix is security-relevant: if 3x-01 is
still waiting for A-03 sign-off, ship this plan alone and record the split in Notes.

## Scope

**In (PD-14 shape):**
- Re-raise the **same exception type** with a redacted message, `from None`, and keep the original exception on an
  attribute:
  - `make_request`: `TelegramNetworkError` with the redacted text, `from None`, original on `.original`.
  - `stream_content`: an `aiohttp.ClientResponseError` (or whatever `ClientError` subclass was raised) whose message
    and URL fields are redacted, `from None`, original on `.original`. The type stays the same, so `except
    aiohttp.ClientResponseError` in user code keeps working.
- Redaction: one private helper that replaces `bot<digits>:<token-chars>` in path segments with `bot<id>:***`, and
  also matches the bare token wherever it appears. Use it in both sites.
- Covers both `__str__` / `repr` and every URL-bearing attribute that aiohttp prints (`request_info.real_url`,
  `request_info.url`).

**Out:**
- Log filters on every `aiogram.*` logger and access-log redaction: H-02 / H-04 (4.0, PD-14 "H owns only the log
  filters").
- The 4.x exception wrapping: D-03.
- Error trackers that capture locals (R22: out of scope).

## Checklist

- [ ] Write a failing test first. Using a fabricated token `123456:AAAA…` (≥ 30 chars), assert it is absent from
      `str(e)`, `repr(e)` and `"".join(traceback.format_exception(e))` for:
  - a connection error in `make_request`;
  - a timeout in `make_request`;
  - a 404 `ClientResponseError` in `stream_content` (use an `aiohttp` test server or a mocked `session.get`).
- [ ] Implement the helper and both re-raise sites (`from None`, `.original`).
- [ ] Check that `__cause__` is `None` and `__suppress_context__` is true on the raised exceptions. The traceback must
      not print the original.
- [ ] Build the copied aiohttp exception with redacted `request_info` and message. If aiohttp's constructor makes
      that impossible for some subclass, wrap it in a subclass of the original type and record the case in Notes.
- [ ] Docs: one paragraph in the errors page: "network errors never contain the token; the original exception is
      available as `.original` and may contain it — don't log it".
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.bugfix.rst`, ending with "Reported by the Anthropic OSS Scanner
      (ANT-2026-4GL80S7S).".
- [ ] Commit trailer `Reported-by: Anthropic OSS Scanner (ANT-2026-4GL80S7S)`, and the id in the commit body.
- [ ] Migration registry: no entry. The 4.0 counterpart (D-03) is not a break.

## Acceptance criteria

- The token never appears in `str`, `repr` or a formatted traceback of the exceptions raised by `make_request` and
  `stream_content`, for connection, timeout and HTTP-status failures.
- `except TelegramNetworkError` and `except aiohttp.ClientResponseError` keep catching the same failures as before.
- `.original` holds the untouched aiohttp exception.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep `__cause__` (scanner fix shape) | A formatted traceback prints the chained cause, so the token still leaks | PD-14, R22 |
| Redact only in `make_request` (scanner patch) | Downloads leak through `stream_content` | — |
| Wrap download errors in `TelegramNetworkError` | Changes the exception type 3.x callers catch | PD-14 |
| Rely on a logging filter only | Python doesn't apply ancestor logger filters to child loggers, and filters don't sanitise formatter-generated exception text | R22 |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
```

## Workflow notes

- D-03 implements the 4.x version (wrapped `from None`, `.original`).
- H-02 adds the log filters.
- Security patch: it goes into a **patch** release as soon as it is merged. It doesn't wait for the 3.x minor that
  carries the behaviour-changing quick wins.

## Notes

- Owner, 2026-11-18: publish through a **GitHub Security Advisory private fork**; the advisory and the patch release
  go out together. The ANT id appears only in the advisory credit: no id in the public commit message, trailer or
  changelog fragment (this overrides the two id checklist items above). Nothing is pushed to the public repo before
  the advisory is published.
- Implementation (fork PR #1): the copied aiohttp exception is built with `cls.__new__(cls, *args)` plus
  `__dict__`, not through the constructor, so one path keeps the exact type for every `ClientError` subclass; no
  subclass wrapping was needed. aiohttp timeout errors carry the URL too and are covered. Follow-up candidate:
  `URLInputFile` source request headers echoed in connection errors (no bot token).
- Owner, later on 2026-11-18: the fix **does** credit the scanner as the checklist says (changelog "Reported by the
  Anthropic OSS Scanner (ANT-…).", a `Reported-by` trailer per finding, credits in the PR body); the bugs are not
  critical enough to hide the credit. Repro code and write-up text still stay out.
- Owner, 2026-11-18: no separate patch release — 3x-19 ships in the single 3.33.0 release together with 3x-15 and 3x-02
  (overrides the Workflow note "goes into a patch release as soon as it is merged").
- Shipped in aiogram 3.33.0; advisory: https://github.com/aiogram/aiogram/security/advisories/GHSA-52j5-qrwv-2vf2.
