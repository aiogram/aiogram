# H-09 — `aiogram[otel]`: metrics with bounded labels

| Field | Value |
|---|---|
| Status | `todo` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-08](H-08-otel-traces.md) |
| Blocks | — |
| Gate-conditional | no |
| Decisions | D64, R23, D22, D47 |
| Sources | [15-observability.md §3 "Metrics"](../../research/15-observability.md), [19 R23](../../research/19-review-resolutions.md), [codex-review.md R23](../../research/codex-review.md), [12-runtime.md §3, §6](../../research/12-runtime.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

D64 includes metrics. R23 requires bounded labels:
- no chat or user ids;
- no ids of bots created on demand;
- unknown method and update-type names capped;
- stable handler names.

Runtime `add_bot` (D22) means even "registered bots" can be unbounded on multi-tenant hosts, so `bot_id` labels are
**opt-in** (planning resolution).

## Scope

**In:** the instruments below, recorded by the H-08 OTel tracer from span enter/exit, with no new hook points:

| Instrument | Type | Attributes | Source |
|---|---|---|---|
| `aiogram.updates` | counter | `update_type`, `outcome` (`handled` / `unhandled` / `error`) | `UPDATE` span exit |
| `aiogram.handler.duration` | histogram (s) | `handler`, `router` | `HANDLER` span |
| `aiogram.api.duration` | histogram (s) | `method`, `status` | `API_CALL` span (per attempt, PD-17) |
| `aiogram.api.errors` | counter | `method`, `reason` | `API_CALL` span with exception |
| `aiogram.runner.inflight` | up-down counter | none by default; `bot_id` only with `setup(..., bot_id_labels=True)` | `UPDATE` span enter/exit |

- **Label bounds:**
  - `update_type` must be in the generated update-type table, otherwise `"unknown"`;
  - `method` must be a generated method name, otherwise `"other"` (raw `bot.call` names, D96);
  - `reason` is an `ErrorReason` value, otherwise `"unknown"`;
  - `handler` is the H-06 stable name;
  - no chat or user ids anywhere.
- `outcome`: `error` when an exception escaped the handler chain, even if an `errors` handler then handled it. If
  the `UPDATE` span doesn't already carry this, add one attribute write in the executor seam from H-06.
- Each instrument has a short description and a unit.

**Out:**
- Exporter and SDK configuration (user).
- Prometheus naming conventions (exporter-side).
- Runner admission-queue metrics (not in D64; 4.x).

## Checklist

- [ ] Instruments created once per `setup` from `meter_provider` (or the global one).
- [ ] Label bounding helpers (known-name tables come from the generated method and update-type tables).
- [ ] **Decide the `router` label for unnamed routers.** 3.x `Router(name=None)` defaults to `hex(id(self))`,
      which changes every process start (proposed default: the explicit `name` if given, else the `__module__` of
      the module that created the router, captured at construction, else `"<anonymous>"`). Record the decision in
      *Notes* and flag it to the owner.
- [ ] `bot_id_labels: bool = False` on `setup` (planning resolution). Docs warn about cardinality on multi-tenant
      hosts.
- [ ] Tests with `InMemoryMetricReader`:
  - [ ] each instrument with expected attributes;
  - [ ] a fuzz of 1 000 random raw method names and unknown update types yields ≤ 1 extra label value each
        (`"other"` / `"unknown"`);
  - [ ] no attribute key is ever a chat or user id field;
  - [ ] `bot_id` appears only with `bot_id_labels=True`;
  - [ ] lambda handlers in two places give two distinct, stable names across two process runs (subprocess test).
- [ ] Docs: metrics table, label bounds, the opt-in `bot_id`.
- [ ] Changelog fragment.

## Acceptance criteria

- The cardinality fuzz stays within the bounds above.
- Instrument names, types and attributes match the table exactly.
- With `bot_id_labels=False`, no metric carries `bot_id`.

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| `bot_id` on `aiogram.runner.inflight` for all registered bots (15 §3) | Runtime `add_bot` makes the registered set unbounded on multi-tenant hosts | planning resolution (opt-in), R23 |
| Labels from `repr()` or object ids | Unstable and unbounded | R23 |
| A separate metrics hook next to the tracer | Spans already carry everything; one hook (D54) | D54, D63 |

## Validation

```bash
make dev
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: H-08's package and `setup`; H-06 stable names; generated method and update-type tables (C-15/C-16
  output, already in the package).
- Can run in parallel with the toolkit lane (H-10…H-18).

## Notes
