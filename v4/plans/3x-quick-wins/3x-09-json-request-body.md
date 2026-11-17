# 3x-09 — JSON request body when there are no files

| Field | Value |
|---|---|
| Status | `todo` |
| Story | 3x — 3.x quick wins & migration baseline |
| Target branch | `dev-3.x` |
| Depends on | [A-05](../A-contracts/A-05-bench-harness.md), [A-09](../A-contracts/A-09-request-oracle.md) (request oracle, used as an invariance check) |
| Blocks | [A-06](../A-contracts/A-06-record-3x-baselines.md), [3x-10](3x-10-webhook-json-reply.md) |
| Gate-conditional | no |
| Decisions | R18 (files → multipart, no files → JSON), PD-28 (behaviour-visible → minor) |
| Sources | [09 #9](../../research/09-3x-quick-wins.md), [05 §1, §2.1](../../research/05-network.md), [19 R18](../../research/19-review-resolutions.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

`AiohttpSession.make_request` always sends `multipart/form-data`, built by `AiohttpSession.build_form_data`. That
function runs the recursive Python `BaseSession.prepare_value` on every field and JSON-encodes nested values into
form strings. A plain `SendMessage` costs 93 µs to encode. JSON in the body instead costs ≈21 µs, about −30% CPU per
API call (05 §1).

## Scope

**In:**
- `make_request` sends `application/json` when the prepared request has **no files**, and multipart otherwise
  (R18).
- The parameter values are identical in both forms: defaults resolved, `None` dropped, the same rules as
  `prepare_value`. Only the encoding differs (nested objects become JSON objects instead of JSON-string fields).
- Fast path only when it is safe: the session class overrides neither `prepare_value` nor `build_form_data`
  (checked via `type(self).prepare_value is BaseSession.prepare_value`, and the same for `build_form_data`).
  Otherwise today's path runs unchanged.
- The default serializer. 09 proposes `pydantic_core.to_json` as the default `json_dumps`. `json_dumps` must keep
  returning `str` for users who call it; to_json returns bytes, so wrap it if adopted.

**Out:**
- Webhook replies: [3x-10](3x-10-webhook-json-reply.md).
- The 4.0 Rust encoder: D-07, D-08.
- PD-08 (session `json_*` no longer affect the wire) is 4.0 only. In 3.x a custom `json_dumps` keeps being used.

## Checklist

- [ ] Baseline with A-05 on `request.sendMessage.plain`, `request.sendMessage.defaults` and
      `request.sendMediaGroup.files`.
- [ ] Implement the has-files detection once, so it can be shared with 3x-10. For example, `prepare_value` already
      collects `files`.
- [ ] JSON path in `make_request`, guarded by the override checks.
- [ ] Decide the default `json_dumps`:
  - proposed default: keep `json.dumps` and use `pydantic_core.to_json` only inside the fast path when the user
    didn't pass `json_dumps`;
  - check the differences (`ensure_ascii`, float formatting, `Default` / `datetime` handling);
  - record the decision in Notes and flag it to the owner if the public default changes.
- [ ] Run the A-09 request oracle, parent vs this commit:
  - resolved params must be invariant for every case;
  - the encoding becomes an approved difference ("json-body", decision R18).
- [ ] Tests:
  - JSON for no files, multipart with an `InputFile`, multipart for nested files in `sendMediaGroup`;
  - an overridden `prepare_value` or `build_form_data` keeps the old path;
  - a custom `json_dumps` is honoured.
- [ ] 100% coverage.
- [ ] Changelog fragment `CHANGES/<pr>.feature.rst`:
  - "Requests without files are sent as JSON";
  - note it for custom servers and proxies that inspect form bodies;
  - ship in a 3.x **minor** (PD-28).
- [ ] Migration registry: no entry (3.x encoding change).

## Acceptance criteria

- A-05 `compare` on `request.sendMessage.plain`: encode median ≥ 3× faster than the parent commit.
- A-09: params invariant for 100% of the request cases; the only differences are encoding, tagged R18.
- Requests with files are byte-for-byte unchanged in part names and filenames.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Always multipart (aiogram_rust) | Larger and slower | 13 §4 |
| Fast path also for overridden `prepare_value` | Breaks subclass behaviour | 09 #9 note |
| Rust encoder in 3.x | 4.0 scope | D5 |

## Validation

```bash
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv run python -m benchmarks compare --base HEAD~1 --head HEAD --cases request.sendMessage.plain,request.sendMessage.defaults,request.sendMediaGroup.files
uv run python -m differential run --kind request --left git:HEAD~1 --right git:HEAD
```

## Workflow notes

- Shares the has-files detection with 3x-10, so land 3x-09 first.
- D-07, D-08 and D-14 keep the same JSON-vs-multipart rule in 4.0.
- Part of the "optimised 3.x" request baseline (A-06).

## Notes
