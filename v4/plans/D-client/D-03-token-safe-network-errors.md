# D-03 — Token-safe network errors (`from None`, `.original`, redacted URLs)

| Field | Value |
|---|---|
| Status | `done` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md), [A-11](../A-contracts/A-11-migration-registry.md) |
| Blocks | [D-05](D-05-download-lifecycle.md), [D-11](D-11-session-on-new-codec.md), [D-16](D-16-cancellation-resource-tests.md), [H-02](../H-testing-observability/H-02-token-redaction-filter.md), [G-13](../G-features/G-13-retry-middleware.md) |
| Gate-conditional | no |
| Decisions | R22, D66, PD-14 |
| Sources | [19 §2 R22](../../research/19-review-resolutions.md), [15-observability.md §5](../../research/15-observability.md), [codex-review.md R22](../../research/codex-review.md), [plans README §1 PD-14](../README.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The bot token is part of every API URL (`/bot<token>/method`, `/file/bot<token>/path`). R22 (verified): aiogram
must never build exception text from aiohttp errors whose `str()` contains the URL, nor keep such an original as
`__cause__`, which every formatted traceback prints. Rule: **aiogram never builds token-bearing exception text.**

PD-14: in 4.x aiohttp errors are wrapped `from None` with the original on `.original` (this plan). This plan also owns the scope formerly planned as H-03 (exception-side redaction);
H owns only log filters (H-02, H-04).

Today (`aiogram/client/session/aiohttp.py`, `AiohttpSession.make_request`): `TimeoutError` →
`TelegramNetworkError("Request timeout error") from e`; `ClientError` →
`TelegramNetworkError(f"{type(e).__name__}: {e}") from e`. `AiohttpSession.stream_content` lets
`ClientResponseError` (`raise_for_status=True`) escape raw.

## Scope

**In:**
- A URL renderer on `TelegramAPIServer` (`aiogram/client/telegram.py`), e.g. `api_url_redacted(bot_id, method)` /
  `file_url_redacted(bot_id, path)`, producing `/bot<id>:***/…`. No regex needed: the bot id is known.
- `AiohttpSession.make_request` and `stream_content`: catch `TimeoutError` and `aiohttp.ClientError` (incl.
  `ClientResponseError` from downloads) and raise `TelegramNetworkError` **`from None`**, original on `.original`,
  message built from the exception type name + a redacted URL + only token-free fields (status, reason phrase).
- `TelegramNetworkError.original: BaseException | None` (documented; not `__cause__`).
- `URLInputFile` reads (`aiogram/types/input_file.py`) go through `stream_content`, so they inherit the wrapping.
- Audit every `raise … from e` and f-string with `e` under `aiogram/client/**`, `aiogram/webhook/**`,
  `aiogram/types/input_file.py` for token-bearing text.
- A reusable test helper (fabricated token, e.g. `"123456:" + "A"*35`) asserting the token is absent from
  `str(exc)`, `repr(exc)`, `"".join(traceback.format_exception(exc))`, and the walked
  `__cause__`/`__context__` chain. H-02 and D-16 reuse it.

**Out:**
- Logging filters (`TokenRedactingFilter` on every `aiogram.*` logger) → H-02; access-log filters → H-04.
- `Bot.__repr__` → D-01.
- Download timeouts / `bot.stream()` → D-05.

## Checklist

- [ ] Redacted URL renderer on `TelegramAPIServer` (+ tests for default and custom/local servers).
- [ ] Wrap aiohttp errors `from None` in `make_request` and `stream_content`; original on `.original`.
- [ ] `TelegramEntityTooLarge` and other `TelegramNetworkError` subclasses keep working.
- [ ] Decide how a network error states whether the request was sent (needed by G-13 to distinguish known
      rejection from ambiguous failure, R19) (proposed default: `TelegramNetworkError.request_sent: bool | None` —
      `False` for `ClientConnectorError`/`ClientProxyConnectionError`/connect-phase timeout, `None` otherwise) —
      record in Notes and flag to owner.
- [ ] Audit and fix token-bearing text in the listed packages.
- [ ] Token-absence test helper + tests for: connection error, read timeout, 4xx/5xx download (`ClientResponseError`),
      `URLInputFile` failure, invalid URL.
- [ ] Tests (100% coverage of new code).
- [ ] Migration-registry entry (PD-13): network errors no longer chain `__cause__`; use `.original`.
- [ ] Changelog fragments: `bugfix` (token-safe errors) and `removal`
      (`__cause__` → `.original`).

## Acceptance criteria

- For each failure mode above, with a fabricated token: the token substring is absent from `str`, `repr`, formatted
  traceback and every chained exception; `exc.__cause__ is None` and `exc.__suppress_context__ is True`.
- `exc.original` is the aiohttp exception instance.
- Message names the exception type and the redacted URL (`/bot<id>:***/`).
- No `raise … from e` with token-bearing `e` remains in the audited packages (grep-checked in the PR description).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep `__cause__`, redact only the outer message | Formatted traceback prints the cause (verified) | R22 |
| Regex-redact exception strings after the fact | aiogram knows the bot id; not building the text is simpler and exact | R22 / 15 §5 |
| Re-raise the same aiohttp type with redacted message (3.x shape) | 3.x keeps types for compat; 4.0 wraps consistently | PD-14 |
| Rely on log filters only | Exceptions are printed outside logging (tracebacks, error trackers) | R22 |

## Validation

```bash
make dev
uv run pytest tests/test_api/test_client
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Outputs: token-absence helper (H-02, D-16), `.original`/`request_sent` (G-13 RetryMiddleware).
- Parallel with D-01, D-02, D-04, D-06.

## Notes
