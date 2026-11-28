# 3x-10 — Webhook: JSON reply when the returned method has no files

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [3x-09](3x-09-json-request-body.md) (shared has-files detection), [3x-02](3x-02-webhook-poison-200.md) (same file, land first), [A-09](../A-contracts/A-09-request-oracle.md) |
| Blocks | — |
| Gate-conditional | no |
| Decisions | R18 (keep multipart for methods with files; applies to 3.x too, D120) |
| Sources | [09 #10](../../research/09-3x-quick-wins.md), [05 §2.4](../../research/05-network.md), [19 R18](../../research/19-review-resolutions.md) |
| Size | S (≤1 day) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`BaseRequestHandler._build_response_writer` (`aiogram/webhook/aiohttp_server.py`) always builds a
`MultipartWriter` for a method returned from a handler, even when it has no files. Telegram accepts a JSON webhook
reply (`{"method": "...", ...params}`), which is smaller and cheaper.

## Scope

**In:**
- No files: return a JSON payload with `method` plus the same resolved params as the multipart path. Prepare values
  through `bot.session.prepare_value`, so defaults resolve as today.
- Files: today's multipart path, unchanged.
- An empty reply stays `JsonPayload({})`.

**Out:** 4.0 webhook reply encoding: D-14.

## Checklist

- [ ] Reuse 3x-09's has-files detection.
- [ ] JSON reply path.
- [ ] Run the A-09 webhook-reply cases, parent vs this commit:
  - params invariant;
  - encoding is an approved difference (R18).
- [ ] Tests:
  - `SendMessage` reply is JSON with the correct content type;
  - `SendPhoto` with `BufferedInputFile` stays multipart;
  - the empty-reply path;
  - a custom `json_dumps` is honoured.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.feature.rst` (3.x minor with 3x-09, PD-28).
- [ ] Migration registry: no entry.

## Acceptance criteria

- A-09 reply cases: params invariant; a JSON content type for 100% of the reply cases without files.
- Every existing `tests/test_webhook` case passes. Tests that assert multipart for file-less replies are updated, and
  the PR lists them.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| JSON for every reply, files dropped or rejected | Breaks inline uploads | R18 |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m differential run --kind request --left git:HEAD~1 --right git:HEAD
```

## Workflow notes

D-14 implements the same rule over the Rust encoder (`JsonBody | Multipart`).

## Notes
