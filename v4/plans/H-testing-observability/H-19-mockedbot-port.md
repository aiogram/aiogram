# H-19 — Port `MockedBot` / `MockedSession` and the suite strategy

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [A-01](../A-contracts/A-01-bootstrap-dev-4x.md) |
| Blocks | [D-11](../D-client/D-11-session-on-new-codec.md), [H-07](H-07-api-call-spans.md), [H-20](H-20-integration-layer-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D88, D52, PD-08, PD-31 |
| Sources | [14-testing.md §3 "Dogfooding"](../../research/14-testing.md), [05-network.md §2.2–2.3](../../research/05-network.md), [README "Breaking changes" 1, 11](../../research/README.md), [19 R06](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D88 says `MockedBot` stays the tool for unit tests of single components, and the toolkit is for new end-to-end
tests; there is no mass rewrite. `tests/mocked_bot.py` is used in about 218 test files, with about 214
`add_result_for` calls. It depends on three things 4.0 changes:
- pydantic `Response[method.__returning__]` (generic model construction);
- `response.model_dump_json()` fed to `check_response`;
- `UNSET_PARSE_MODE` as a default (the `UNSET_*` sentinels are removed, README breaking change 11).

This task is pulled forward (PD-31). Every story's unit tests need a `MockedBot` that survives the model and codec
switch, so the port isolates that dependency behind one seam **before** D-11 swaps the codec.

## Scope

**In:**
- `tests/mocked_bot.py`:
  - **Public test API unchanged:** `MockedBot(**kwargs)`, `add_result_for(method, ok, result=None,
    description=None, error_code=200, migrate_to_chat_id=None, retry_after=None)`, `get_request()`,
    `session.requests`, `session.closed`. The 214 call sites don't change.
  - `MockedSession` stores plain response records (no `Response[T]`). `make_request` builds the wire envelope
    `{"ok", "result", "description", "error_code", "parameters"}` as JSON bytes and passes it through the
    session's **public response-check path**. That is `check_response` today; after D-11/PD-08, whatever D-11
    defines as the decode entry. Unit tests keep exercising the real response mapping, as in 3.x.
  - One private helper turns `result` into wire JSON. It uses the 3.x serialisation while `aiogram.types` is
    pydantic and `to_dict()` once C-13 switches the types. This helper is the only line that changes at the
    switch, and it carries a comment naming C-13.
  - `make_request(..., timeout: int | None = None)`: no `UNSET_PARSE_MODE`. The token is passed by keyword.
- `tests/conftest.py`:
  - `bot` and storage fixtures unchanged;
  - the `dispatcher` fixture keeps `emit_startup`/`emit_shutdown` through the E-18 compatibility path. If E-18
    changes that, it updates this fixture.
- **Suite strategy (D88)**, written into `AGENTS.md` ("Testing" section) and the contributor docs:
  - `MockedBot` for unit tests of one component;
  - `aiogram.test` toolkit for end-to-end scenarios (dispatcher + FSM + scenes + filters + errors);
  - no mass rewrite of existing tests;
  - 100% coverage rule unchanged.
- Guard test: `tests/mocked_bot.py` imports nothing from `pydantic`.

**Out:**
- The toolkit (H-10…H-17).
- The new decode path itself (D-09/D-11).
- Porting individual tests that use removed APIs: each owning story ports its own tests.

## Checklist

- [ ] Rewrite `MockedSession` / `MockedBot` per Scope, keeping the public test API.
- [ ] Single wire-serialisation helper with the C-13 switch comment.
- [ ] Guard: no `pydantic` import in `tests/mocked_bot.py`.
- [ ] Self-tests for `MockedBot`:
  - [ ] success result;
  - [ ] `ok=False` with `error_code=400` raises `TelegramBadRequest`;
  - [ ] `retry_after` raises `TelegramRetryAfter`;
  - [ ] `migrate_to_chat_id` raises `TelegramMigrateToChat`;
  - [ ] requests are recorded in order.
- [ ] Run the full suite unchanged (no call-site edits).
- [ ] `AGENTS.md` testing section + contributor docs paragraph.
- [ ] No changelog (test-only), no registry entry.

## Acceptance criteria

- `uv run pytest tests` passes on `dev-4.x` with zero edits to `add_result_for` call sites.
- `grep -n pydantic tests/mocked_bot.py` is empty.
- When D-11 lands, its PR changes at most the serialisation helper and the decode-entry call in
  `tests/mocked_bot.py` (D-11 reviewer checks this).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Rewriting unit tests onto the toolkit | No mass rewrite | D88 |
| Returning `result` directly without the response path | Unit tests would stop exercising error mapping (`TelegramBadRequest`, `RetryAfter`), which 3.x tests rely on | D88 (keep 3.x semantics) |
| Keeping `Response[T]` (pydantic generic) | Types are no longer pydantic; aiogram drops pydantic | D12–D15 |

## Validation

```bash
uv sync --locked --all-extras --group dev --group test
make dev            # once B-01 has landed
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Pulled forward (PD-31). Start right after A-01.
- Consumers: every story's unit tests. D-11 must keep it working (it touches only the seam). H-07 and H-20 use it
  directly.

## Notes
