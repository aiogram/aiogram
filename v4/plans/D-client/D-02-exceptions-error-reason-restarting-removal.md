# D-02 — Exceptions: `ErrorReason` on `e.reason`, `RestartingTelegram` removal, `ClientDecodeError.raw`

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md), [A-11](../A-contracts/A-11-migration-registry.md), [C-12](../C-butcher/C-12-enums-error-reason-emitter.md) |
| Blocks | [D-09](D-09-response-decoder.md), [D-11](D-11-session-on-new-codec.md), [G-13](../G-features/G-13-retry-middleware.md), [H-07](../H-testing-observability/H-07-api-call-spans.md), [H-17](../H-testing-observability/H-17-toolkit-feature-interop.md) |
| Gate-conditional | no |
| Decisions | D47, PD-24, PD-29, 11 §2 |
| Sources | [03-routing.md §5 D47](../../research/03-routing.md), [10-forward-compatibility.md §3 Layer 2](../../research/10-forward-compatibility.md), [11-removals.md §2](../../research/11-removals.md), [02-butcher.md §5](../../research/02-butcher.md), [19](../../research/19-review-resolutions.md), [plans README §1](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D47: API errors get a reason enum, not new exception classes. `except TelegramBadRequest` keeps working, and
`e.reason is ErrorReason.MESSAGE_NOT_MODIFIED` replaces substring matching on `e.message`. `RestartingTelegram` is
dead ("not used by Telegram anymore", 11 §2). Layer 2 of forward compatibility needs a decode error that carries the
raw `result` so callers can recover; PD-29 keeps `ClientDecodeError` and adds `.raw` instead of the
`TelegramDecodeError` named in 10.

Today the mapping lives inline in `BaseSession.check_response` (`aiogram/client/session/base.py`), interleaved with
pydantic decoding. The Rust decoder (D-09) hands Python an error tuple, so the mapping must become a standalone
function.

## Scope

**In:**
- New module-level function (e.g. `aiogram/client/session/errors.py: raise_for_error(method, status_code,
  error_code, description, parameters) -> NoReturn`) holding the exact 3.x mapping now in `check_response`:
  `retry_after` → `TelegramRetryAfter`, `migrate_to_chat_id` → `TelegramMigrateToChat`, 400/404/409/401/403/413/5xx
  → the existing classes, else `TelegramAPIError`. `check_response` calls it (still pydantic-backed until D-09).
- `TelegramAPIError` (`aiogram/exceptions.py`) gains:
  - `reason: ErrorReason | None` — lazy on first access: exact lookup of `description`, then the template regexes
    from the generated table; `None` for unknown messages.
  - `reason_args: tuple[str, ...]` — values captured by the matching `%s`/`%d` template.
  - `error_code: int | None`, `status_code: int | None` (needed by H-07 metrics and G-13).
- Consume `aiogram/enums/error_reason.py` (`ErrorReason` `StrEnum` + template table) emitted by C-12; member names
  are pinned by the overlay (PD-24).
- Remove `RestartingTelegram` from `aiogram/exceptions.py` and the `"restart" in description` branch; such
  responses raise `TelegramServerError` (reason via `ErrorReason` if `errors.json` has it).
- `ClientDecodeError` gains `.raw: bytes | None` = the raw `result` (method call) or raw body (envelope failure)
  (PD-29). Existing `.message`, `.original`, `.data` stay.
- Remove `UnsupportedKeywordArgument` only if E-01 hasn't already (it lives in the same file; coordinate, do not
  duplicate).

**Out:**
- Producing the error tuple from Rust → D-09.
- `ErrorReason` generation from `errors.json` → C-05 / C-12.
- Router `errors` bubbling and `ErrorEvent` fields → E-11.
- Network exceptions (`TelegramNetworkError` wrapping) → D-03.

## Checklist

- [ ] Extract the status/parameters → exception mapping into one function; `check_response` delegates to it.
- [ ] Add `reason`, `reason_args`, `error_code`, `status_code` to `TelegramAPIError`; `reason` resolved lazily and
      cached on the instance.
- [ ] Wire the C-12 table; until C-12 lands, develop against a small hand-written fixture table under `tests/`
      (the PR merges only after C-12).
- [ ] Remove `RestartingTelegram` and its branch; update `tests/test_api/test_client/test_session/test_base_session.py`.
- [ ] Add `ClientDecodeError.raw`.
- [ ] Decide what `ClientDecodeError.raw` holds when the envelope itself is not JSON (proposed default: the full
      response body bytes; `result` slice when the envelope parsed) — record in Notes and flag to owner.
- [ ] Docs: errors page gains an `e.reason` section with the two usage forms from D47
      (`except … if e.reason is …`, `@router.errors(F.exception.reason == …)`).
- [ ] Tests (100% coverage of new code): every status branch, exact match, template match with args, unknown → `None`.
- [ ] Migration-registry entry (PD-13): `RestartingTelegram` removed (kind `removal-4.0`, replacement
      `TelegramServerError`).
- [ ] Changelog fragments: `removal` (RestartingTelegram), `feature` (`e.reason`).

## Acceptance criteria

- `TelegramBadRequest(method, "Bad Request: message is not modified: …").reason is ErrorReason.MESSAGE_NOT_MODIFIED`.
- A templated message yields the matching member and non-empty `reason_args`.
- An unknown description yields `reason is None` and never raises.
- `reason` is computed at most once per exception instance (test via a counting table stub).
- `from aiogram.exceptions import RestartingTelegram` raises `ImportError`; a 5xx with "restart" raises
  `TelegramServerError`.
- `ClientDecodeError.raw` is set on decode failures.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| One exception class per error message | Breaks `except` hierarchies, 945 classes | D47 |
| New `TelegramDecodeError` class | No new classes; `ClientDecodeError` already exists | PD-29 |
| Keep `RestartingTelegram` as deprecated alias | Telegram no longer sends it; reason enum covers it | 11 §2 |
| Eager reason matching at construction | Regex cost on every error even when nobody reads it | D47 ("lazy on first access") |

## Validation

```bash
make dev
uv run pytest tests/test_api/test_client
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: C-12 (`aiogram/enums/error_reason.py`).
- Outputs: `raise_for_error(...)` used by D-09/D-11; `status_code`/`reason` used by G-13 (Retry) and H-07/H-09.
- Parallel with D-01, D-03..D-06.

## Notes
