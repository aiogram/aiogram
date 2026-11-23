# H-02 — Token redaction filter

| Field | Value |
|---|---|
| Status | `done` |
| Story | H — Testing & observability |
| Target branch | `dev-4.x` |
| Depends on | [H-01](H-01-logger-hierarchy.md), [D-03](../D-client/D-03-token-safe-network-errors.md) |
| Blocks | [H-04](H-04-access-log-redaction.md), [H-16](H-16-fake-fidelity.md), [H-20](H-20-integration-layer-exit-gate.md) |
| Gate-conditional | no |
| Decisions | D66, R22, PD-14, PD-31 |
| Sources | [15-observability.md §5](../../research/15-observability.md), [19 R22 + "New issues"](../../research/19-review-resolutions.md), [codex-review.md R22, §11](../../research/codex-review.md) |
| Size | M (2–3 days) |

> **Session handoff.** This plan is self-contained: it can be given to a fresh session as its only instruction, or
> run as one step of an orchestrated workflow. Read the *Sources* first; where a source disagrees with
> [19-review-resolutions.md](../../research/19-review-resolutions.md), 19 wins. Do not change the research pages; if
> the plan turns out to be wrong, stop and record the problem under *Notes* instead of improvising a new decision.

## Motivation

The bot token is in every API URL (`/bot<token>/method`) and in `TokenBasedRequestHandler` webhook paths. Network
exception texts can carry URLs. D66
makes redaction **on by default**.

R22 found the original design ineffective, for two reasons. A filter on the `aiogram` logger does not apply to
records from child loggers, because Python never runs ancestor *logger* filters. And editing `msg`/`args` does not
touch formatter-generated text. This task puts the filter on **every** `aiogram.*` logger and proves it with a test
that walks the logger dict. It is pulled forward (PD-31) so every later task logs through it.

## Scope

**In:**
- `TokenRedactingFilter(logging.Filter)` in `aiogram/loggers.py`, installed by the H-01 factory on every framework
  logger at creation.
- Pattern: `\d{5,}:[A-Za-z0-9_-]{30,}`, replaced with `<id>:***` (the bot id is kept).
- Rewrites a record **only when a token matches**, so Sentry grouping by message template is preserved for
  ordinary records.
- What it scans:
  - **message**: `record.getMessage()` is computed once. On a match, `record.msg` is set to the redacted text and
    `record.args = ()`. This covers non-`str` args such as `yarl.URL` and exceptions.
  - **exception text**: when `exc_info` is set, the formatted traceback is checked. On a match, the redacted text
    goes to `record.exc_text`, so standard formatters print the redacted version. This is defence in depth: D-03
    guarantees aiogram never builds token-bearing exception text.
  - **`stack_info`**.
  - **string attributes added through `extra=`**, one level of nested `dict[str, str]` included. aiohttp's
    `AccessLogger` passes request fields such as `first_request_line` this way (`aiohttp/web_log.py`), and JSON
    formatters emit them. This is a **proposed default that extends 15 §5 / 19 R22**; flag it to the owner.
- It **never raises**: any internal error lets the record through unchanged and is reported once through
  `warnings.warn`, never through logging (no recursion). It never drops a record.
- Opt-out: `aiogram.loggers.redact_tokens(False)` flips a module-level flag that the filter reads. No filter
  removal is needed, and it is thread-safe for free-threaded builds.
- The same class is exported for user **handlers** (`handler.addFilter(TokenRedactingFilter())`), which is how
  third-party and root records get covered.
- Logger-dict walk test: import every `aiogram` submodule (`pkgutil.walk_packages`; the test env has all
  extras). Then assert that every `aiogram.*` entry in `logging.Logger.manager.loggerDict` that is a `Logger`
  (not a `PlaceHolder`) has the filter.

**Out:**
- Token-free exception construction, URL rendering `/bot<id>:***/` and aiohttp errors wrapped `from None` with
  `.original`: **D-03** owns that guarantee (H-03 merged into D-03). This plan only tests that the filter adds
  defence in depth.
- `Bot.__repr__` showing only the id: **D-01**.
- Attaching the filter to `aiohttp.access` / `uvicorn.access`: H-04.
- Error trackers that capture locals: out of scope (15 §5).

## Checklist

- [ ] `TokenRedactingFilter`, `redact_tokens(enabled: bool)`, the compiled pattern, and factory wiring (H-01).
- [ ] Redaction of message+args, `exc_text`, `stack_info` and string/dict `extra` attributes, applied only on match.
- [ ] Logger-dict walk test, and a test that a logger created through the factory *after* import also gets the
      filter.
- [ ] Tests with a fabricated token (`123456789:AAAA…` × 35 chars), checking that it doesn't appear in:
  - [ ] a record emitted from a **child** logger (`aiogram.client`, `aiogram.client.x`);
  - [ ] args holding a `yarl.URL` / exception;
  - [ ] `exc_info` with a **chained** exception whose cause text has the token (the R22 probe);
  - [ ] a JSON formatter (`json.dumps(record.__dict__ …)` in a test handler) over `extra` fields, including a
        nested dict;
  - [ ] `stack_info`.
- [ ] Non-matching record: `record.msg` and `record.args` are the **same objects** after filtering (grouping
      preserved).
- [ ] Opt-out test. Test that a filter-internal failure (monkeypatched pattern raising) still passes the record and
      emits one warning.
- [ ] Microbenchmark in the PR description: filter cost per non-matching record with 2 args, so the ceiling is
      known.
- [ ] Docs: "Token redaction" section covering what is covered (framework loggers), what needs the exported
      handler filter (root/third-party handlers), the opt-out, and that user content shaped like a token is masked
      too.
- [ ] Changelog fragment (redaction on by default changes framework log output).

## Acceptance criteria

- The walk test fails when a framework logger without the filter exists (verified by a deliberate negative case in
  the test).
- No fabricated token appears in the output of `logging.Formatter` or a JSON formatter for any of the cases above.
- Records without a token are left untouched (identity check on `msg`/`args`).
- `redact_tokens(False)` turns redaction off for every framework logger at once, and `True` turns it back on.
- The filter never raises out of `filter()` (fault-injection test).

## Rejected alternatives

| Alternative | Why rejected | Decision |
|---|---|---|
| One filter on the `aiogram` parent logger (original 15 §5) | Ancestor logger filters don't run for child records (R22, reproduced) | R22 |
| Redacting `msg`/`args` only | Formatter-generated exception text and `extra` fields still leak | R22 |
| Always rewriting `msg` to the formatted string | Breaks Sentry grouping for every record | R22 |
| A global `logging.setLogRecordFactory` | Changes records for every library in the process; libraries must not own the record factory | D66 scope |
| Keeping the original exception on `__cause__` | A formatted traceback prints the cause (R22 probe) | PD-14, D-03 |

## Validation

```bash
make dev            # once B-01 has landed; pure Python otherwise
uv run pytest tests
uv run mypy aiogram
make lint
```

## Workflow notes

- Inputs: the H-01 factory.
- Outputs:
  - the filter class used by H-04 (access logs) and by the CLI (G-16);
  - the pattern, used by A/H-16 to redact recorded traces before they are committed (R26 provenance).
- Runs in parallel with D-03, which removes tokens from exception text. Keep the URL rendering format (`<id>:***`)
  identical in both places.

## Notes
