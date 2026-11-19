# D-12 — Custom-session hook compatibility (`prepare_value`, `check_response`, third-party sessions)

| Field | Value |
|---|---|
| Status | `todo` |
| Story | D — Client & wire |
| Target branch | `dev-4.x` |
| Depends on | [D-11](D-11-session-on-new-codec.md) |
| Blocks | [D-15](D-15-request-response-differential-cases.md), [H-12](../H-testing-observability/H-12-toolkit-model-api-migration.md) |
| Gate-conditional | yes (assumes the milestone B gate passes, D104; re-validate after B-13) |
| Decisions | 05 §2.3, R18, PD-08, D1, D91, D95 |
| Sources | [05-network.md §2.3](../../research/05-network.md), [codex-review.md R18](../../research/codex-review.md), [19 §2 R18](../../research/19-review-resolutions.md), [01-models.md §3.7](../../research/01-models.md), [08-build-release.md §5](../../research/08-build-release.md), [plans README §1 PD-08](../README.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

05 §2.3 promises that users' httpx/other sessions keep working and that `prepare_value` / `check_response` stay
overridable. R18 points out that the old Python fallback relied on `model_dump()` field walking, which no longer
exists in that form (D95: no field introspection; D1: no pure-Python encoder), and that overridden `check_response`
was never covered. PD-08 already removes JSON hooks from the wire, so what is left is:
1. sessions that override `prepare_value`;
2. sessions that override `check_response` (today: `check_response(bot, method, status_code, content: str) ->
   Response[T]`);
3. third-party `make_request` implementations written against 3.x (they typically call `method.model_dump()` and
   `self.prepare_value`, then `self.check_response`).

The milestone D exit gate requires "hook compatibility" tests (README D121).

## Scope

**In:**
- Detection, once per session subclass, of overridden `prepare_value` / `check_response` (compare to the base
  attributes); behaviour defined by the two Decide items below. Tests must show the override **runs**, not only that
  identity is checked (R18).
- `check_response` compatibility: the default path feeds the D-09 decoder; an overriding subclass receives the
  documented argument types and returns a plain `aiogram.methods.Response[T]` (D-09).
- Old-style `make_request`: works through the deprecated `model_dump()` alias (D91) for one deprecation window;
  documented migration to `self.encode_request(...)` / `self.decode_response(...)` (D-11).
- A test-only httpx-style example session (no new dependency: implement against a fake transport) used as the
  reference "custom session" in tests and docs.
- Docs page "Custom sessions" (client section): minimal subclass, `encode_request`/`decode_response`, which hooks are
  deprecated.

**Out:**
- Default request path → D-11. FakeTelegramSession in the testing toolkit → H-10/H-19 (consume this contract).

## Checklist

- [ ] Decide the `prepare_value` slow path (proposed default: when overridden, the encoder first produces the wire
      builtins per top-level field (same walk as `to_dict()`, files extracted), then the override is applied to each
      top-level value before the final JSON/multipart write; one `AiogramDeprecationWarning` per class; no
      separate Python encoder) — record in Notes and flag to owner.
- [ ] Decide the `check_response` contract (proposed default: signature unchanged except `content: bytes | str`
      (bytes on the default path); when overridden, the session calls it instead of `decode_response` and uses the
      returned `Response.result`; deprecated in favour of a request middleware) — record in Notes and flag to owner.
- [ ] Resolve 08 §5's "request encoding, Rust vs the Python fallback encoder" harness: with the proposed defaults
      there is no Python fallback encoder (D1); record in Notes that D-15 has no such leg.
- [ ] Old-style `make_request` via `model_dump()` alias covered by a test session copied from a 3.x-style httpx
      implementation.
- [ ] Reference custom session (tests) + docs page.
- [ ] Tests (100% coverage of new code): each override runs and affects the sent body / returned result.
- [ ] Migration-registry entries (PD-13, `deprecation-4.x`): overriding `prepare_value`; overriding
      `check_response`; calling `method.model_dump()` in `make_request`.
- [ ] Changelog fragment (`removal`/deprecation).

## Acceptance criteria

- A subclass overriding `prepare_value` to upper-case `text` sends `"TEXT"`; warning emitted once per class.
- A subclass overriding `check_response` receives bytes on the default path and its returned `Response.result` is
  what `bot(method)` returns.
- The 3.x-style httpx-shaped test session (calling `method.model_dump()` + `prepare_value` + `check_response`) can
  send `sendMessage` and `sendPhoto` successfully, with deprecation warnings only.
- A default session never calls `prepare_value` or `check_response` (spy test).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Keep a full Python encoder as fallback | No pure-Python fallback; would need field introspection | D1, D95 |
| Drop `prepare_value`/`check_response` overrides outright | 05 §2.3 promises custom sessions keep working | 05 §2.3 |
| Honour JSON hooks in the compat path | Hooks no longer affect the wire | PD-08 |

## Validation

```bash
make dev
uv run pytest tests/test_api/test_client/test_session
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: D-11 public helpers, D-09 `Response[T]`.
- Outputs: custom-session contract for H-10/H-19 (fake session) and D-15 (custom-session differential cases).

## Notes
