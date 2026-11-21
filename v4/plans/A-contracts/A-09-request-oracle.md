# A-09 — Request/response oracle, 3.x side

| Field | Value |
|---|---|
| Status | `done` |
| Story | A — Contracts & baselines |
| Target branch | `dev-3.x` (merged forward to `dev-4.x`, PD-12) |
| Depends on | [A-04](A-04-pinned-corpus.md), [A-07](A-07-differential-framework.md) |
| Blocks | [3x-09](../3x-quick-wins/3x-09-json-request-body.md), [3x-10](../3x-quick-wins/3x-10-webhook-json-reply.md), [D-15](../D-client/D-15-request-response-differential-cases.md) |
| Gate-conditional | no |
| Decisions | R18, R26, D96–D99, PD-08, PD-11 |
| Sources | [05 §1, §2.1–2.4](../../research/05-network.md), [19 R18](../../research/19-review-resolutions.md), [codex-review R18, R26](../../research/codex-review.md), [13 B8, B17](../../research/13-aiogram-rust-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The 4.0 Rust encoder (D-07 / D-08), the response decoder (D-09) and webhook replies (D-14) must reproduce what 3.x
sends and accepts. The only differences allowed are the decided ones: JSON vs multipart (R18), keyword-only
signatures (D100), timedelta as absolute time (PD-11). aiogram_rust's native and fallback encoders disagreed on 12 of
300 requests (13 B8), which is why this is a separate oracle.

The oracle must exercise **real public entry paths** (R26): what actually goes over HTTP, not internal helpers.

## Scope

**In:** `differential/sides/aiogram3/request.py` and its manifest. Cases come from A-04 `requests/*.toml` plus the
probes below. Each request case is sent through `bot(method)` to a local `aiohttp.test_utils.TestServer` that
plays the Bot API: `Bot(..., session=AiohttpSession(api=TelegramAPIServer.from_base(<test server>)))`. The server
captures the raw HTTP request and answers with an A-04 response fixture.

| Probe | Records |
|---|---|
| `request.resolved` | **Encoding-independent** canonical params: decode JSON bodies, or parse multipart (field → value, nested JSON-string fields decoded); files as `{field, filename, sha256, content_type}`; defaults resolved; `None`s dropped |
| `request.encoding` | `json` or `multipart`, the content type, and the part order for multipart |
| `request.defaults` | the same method under three `DefaultBotProperties` variants (none, `parse_mode`, `link_preview` + `protect_content`) |
| `request.hooks` | the same requests through (a) a `BaseSession` subclass overriding `prepare_value`, (b) a request middleware that rewrites a param, (c) a custom `json_dumps` |
| `request.datetime` | `datetime` (aware / naive), `timedelta` (`until_date`), floats, very large ints, non-ASCII text |
| `response.decode` | each A-04 response fixture through `bot(method)` → result dump, or exception class plus attributes (`error_code`, `description`, `retry_after`, `migrate_to_chat_id`) |
| `webhook.reply` | `BaseRequestHandler._build_response_writer` (through a test-client POST) for a handler returning a method without files and one with files: encoding plus `request.resolved` of the reply |
| `serialize` | `deserialize_telegram_object(method)` output |

- Manifest entries for known differences:
  - `request.encoding`: `json` when there are no files, `approved`, decision R18 (3x-09 for 3.x vs 3.x; D-07 / D-08
    for 4.0);
  - `request.hooks` custom `json_dumps`: no effect on the wire in 4.0 (PD-08);
  - `request.datetime` timedelta encodes `now + delta` (PD-11, invariant: 4.0 must match 3.x);
  - positional construction is impossible in 4.0 (D100). The 3.x side always uses keywords, so this stays
    invariant.
- Poison support: `--poison` drops one resolved param per request.

**Out:**
- The 4.0 adapter and cases: D-15.
- Download and upload lifecycle and cancellation: D-16.

## Checklist

- [ ] Fake Bot API server fixture (aiohttp `TestServer`) recording raw requests. It must not depend on
      `tests/mocked_bot.py`, which isn't installed with the side.
- [ ] Canonicaliser for multipart and JSON bodies, shared with D-15 later. Keep it in `differential/trace.py` or a
      sibling module.
- [ ] Implement all probes over the A-04 request and response inputs.
- [ ] Run `pypi:aiogram==3.32.0` vs `path:.`: 0 mismatches. Run `--poison right`: detected.
- [ ] Manifest entries above.
- [ ] Changelog: none. Use the `skip news` label.

## Acceptance criteria

- Every A-04 request input yields `request.resolved` + `request.encoding` records, and every response input yields a
  `response.decode` record.
- The 3.32.0 vs HEAD run is clean, and poison is detected.
- When run against 3x-09's branch, the only differences are `request.encoding` (approved, R18).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Compare `build_form_data` output directly | Not the public path; misses JSON bodies and session hooks | R26 |
| Use the Testing World fake as the oracle | It intercepts typed methods and never runs the encoder | D52, R26 |

## Validation

```bash
uv run python -m differential run --kind request --left pypi:aiogram==3.32.0 --right path:.
uv run python -m differential run --kind request --left pypi:aiogram==3.32.0 --right path:. --poison right; test $? -ne 0
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
```

## Workflow notes

- **Outputs:** the request/response 3.x trace and the canonicaliser, which D-15 builds the 4.0 side on.
- 3x-09, 3x-10 and 3x-13 use this oracle as their invariance check.

## Notes
