# A-04 — Pinned corpus and payload manifest

| Field | Value |
|---|---|
| Status | `in-progress` |
| Story | A — Contracts & baselines |
| Target branch | `dev-3.x` (merged forward to `dev-4.x`, PD-12) |
| Depends on | — |
| Blocks | [A-05](A-05-bench-harness.md), [A-07](A-07-differential-framework.md), [A-08](A-08-model-oracle.md), [A-09](A-09-request-oracle.md), [A-10](A-10-routing-oracle.md), [3x-08](../3x-quick-wins/3x-08-butcher-literal-tags.md), [3x-17](../3x-quick-wins/3x-17-formatting-perf.md), [B-00](../B-spike/B-00-freeze-gate-spec.md), [B-02](../B-spike/B-02-bench-adapter-memory-estimator.md), [A-06](A-06-record-3x-baselines.md), [C-21](../C-butcher/C-21-generated-tests-emitter.md), [H-16](../H-testing-observability/H-16-fake-fidelity.md) |
| Gate-conditional | no |
| Decisions | PD-12, R26, R04, 13 B24, codex-review §10 |
| Sources | [01 §1, §5](../../research/01-models.md), [03 §2](../../research/03-routing.md), [13 §1, B8, B24](../../research/13-aiogram-rust-review.md), [14 §3 Fidelity](../../research/14-testing.md), [codex-review §10, R26](../../research/codex-review.md), [10 §1](../../research/10-forward-compatibility.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

Milestone A's gate is "oracle + benchmarks exist before any optimisation". Both need **one set of pinned inputs**,
with hashes and provenance, so that:
- every 3.x quick win (D120) is measured on the same data;
- the B gate (B-13) compares 4.0 with optimised 3.x on identical bytes;
- the differential oracles (A-07..A-10) replay identical cases.

The README's numbers came from ad-hoc payloads that are not in the repository, so they can't be reproduced. Codex
§10: store payload hashes, use the real paths (B24) and add hand-curated wire fixtures plus redacted recorded traces
(R26).

## Scope

**In.** Proposed layout (record any change in Notes; A-05 and A-07 follow it):

```
benchmarks/corpus/
  MANIFEST.toml           # one [[input]] per file: id, path, kind, sha256, provenance, bot_api, notes
  wire/<id>.json          # Telegram payloads (updates, responses)
  routing/<id>.toml       # declarative router topologies + the update ids to feed
  requests/<id>.toml      # method name + params (+ file fixtures by reference)
  files/                  # small binary fixtures for uploads
  entities/               # filled by 3x-17
benchmarks/record/        # recorder + redactor for real traces (dev tool, not shipped)
```

**Inputs.** The names are stable ids that plans cite.

| Kind | Ids |
|---|---|
| Decode | `update.text.small`, `update.realistic` (≈2.5 KB / ≈30 models, matching the shape described in 01 §1), `update.message.wide-sparse`, `update.media.large` (big photo sizes and long entities), `update.richtext`, `update.callback`, `update.inline-query` |
| Forward-compat | `update.unknown-tag` (unknown `ChatMember` status), `update.unknown-type` (unknown update key), `update.unknown-field`, `update.unknown-enum`, `update.malformed-member` (a malformed member of a decoded union), `update.deep-nesting` (pinned_message chain) |
| Responses | `response.getUpdates.100` (envelope with 100 mixed updates drawn from the decode set), `response.sendMessage`, `response.error.400`, `response.error.429` (`retry_after`), `response.ok-null-result` |
| Routing | `routing.1-handler`, `routing.20-ftext`, `routing.100-commands`, `routing.5routers-30handlers` (13 §1); `routing.52-handlers` (03 §2: dp→r1→r2→r3, 26 `Command` + 26 `F.text ==`, 2 outer + 2 inner middlewares, events hitting first / mid / last / unhandled). FSM-on and FSM-off variants |
| Requests | `request.sendMessage.plain`, `request.sendMessage.defaults` (parse_mode / link_preview / protect_content defaults), `request.sendPhoto.upload`, `request.sendMediaGroup.files` (nested files), `request.raw-extra-kwargs` |
| Utils | `keyboard.inline.30`, `keyboard.inline.100`, `formatting.nested`, `entities.unparse`, `callback_data.filter.miss`, `utils.deserialize` |
| FSM / misc | `fsm.memory.stateless-read`, `isolation.simple.lock`, `import.aiogram` (a subprocess case, no data) |

- **Recorded traces (R26):**
  - a request-middleware recorder for real bots, which writes request/response pairs and received updates;
  - the redactor replaces the token with `<id>:***`, pseudonymises user and chat ids consistently, replaces names,
    usernames and phones, and strips file ids' unique parts;
  - each recorded file's provenance records the date, aiogram and Bot API version, and "recorded + redacted".
- **Integrity test** (in `tests/`, so it runs in CI):
  - every manifest entry exists and its sha256 matches;
  - every file is in the manifest;
  - no corpus file matches the token regex `\d{5,}:[A-Za-z0-9_-]{30,}`.

**Out:**
- Bench case code: A-05.
- Trace and oracle code: A-07..A-10.
- Entity layouts: 3x-17.

## Checklist

- [ ] Create the layout and the `MANIFEST.toml` schema. Fields: `id`, `path`, `kind`, `sha256`, and
      `provenance = {source = "hand" | "recorded" | "synthesised", date, aiogram, bot_api, author}`.
- [ ] Hand-write or synthesise the decode, forward-compat and response payloads. Validate the known-schema ones with
      3.x (`Update.model_validate_json`) and record which ones 3.x *rejects*: the forward-compat set must fail on
      3.x today, and that is the point.
- [ ] Routing TOML schema: a declarative topology (routers, handler kinds and filter specs, middleware slots, flags)
      plus an ordered event list referencing wire ids. It must be buildable by a 3.x adapter (A-10) and later by a
      4.0 adapter, so it must not encode 3.x API calls.
- [ ] Request TOML schema: method, params, and file references to `files/`.
- [ ] Recorder and redactor in `benchmarks/record/`, with a unit test that a fabricated token, user id and phone are
      redacted, and that pseudonymisation is stable within a trace.
- [ ] Ask the owner whether to record real traces now. Proposed default: one maintainer-run recording session of a
      test bot (≈200 updates covering the decode kinds), committed after redaction review. Record the result in Notes.
- [ ] Integrity test in `tests/test_corpus_manifest.py`.
- [ ] Packaging: `benchmarks/` is excluded from sdist and wheel. Check the hatch config and verify.
- [ ] Changelog: none (dev tooling). Use the `skip news` label.

## Acceptance criteria

- `MANIFEST.toml` lists ≥ 35 inputs, covering every id in the table above.
- The integrity test passes, and the token regex finds nothing.
- Every forward-compat input fails to decode on 3.32.0, and every known-schema input decodes, as recorded in the
  manifest `notes`.
- `benchmarks/` is absent from the built wheel and sdist.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| Reuse the ad-hoc payloads behind the README numbers | Not in the repo, no hashes; not comparable | codex-review §10 |
| Corpus on `dev-4.x` only | 3.x quick wins need it now | PD-12 |
| Unredacted real traces | Token and PII exposure | R26, R22 |
| Payloads from aiogram_rust | Different machine and baseline; lessons, not data | 13 §1, codex-review §10 |

## Validation

```bash
uv run pytest tests/test_corpus_manifest.py -q
uv run pytest tests --cov=aiogram --cov-report=term-missing
make lint
uv build && unzip -l dist/aiogram-*.whl | grep -c benchmarks || true   # must print 0
```

## Workflow notes

- **Outputs:** the input ids used by A-05 bench cases, A-07..A-10 oracle cases, B-00 / B-02 (gate inputs),
  D-15 / E-21 (differential cases), C (strict-mode corpus replay, 10 "Visibility") and 3x-08 / 3x-17.
- Inputs are append-only once A-06 records a baseline on them. A change means a new id.

## Notes

- Owner, 2026-11-18: record real traces now (default). One maintainer-run session of a test bot (≈200 updates), the
  owner runs the bot; the worker prepares the recorder, says what to send, and commits only after the redaction review.
