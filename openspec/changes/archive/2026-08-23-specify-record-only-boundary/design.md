## Context

The toolkit's three-tier ladder — override, model, synthesize — means an unmodeled method
never breaks a test; it just does nothing. That is the property that lets the package
survive Bot API bumps, and it is deliberately generous.

The cost of that generosity is that "unmodeled" carries no information. The research behind
the plan sorted every method into model / seed / record-only with a reason each, but that
sorting lived in a planning document that is now archived. What shipped is the mechanism,
not the judgement.

## Goals / Non-Goals

**Goals:**

- Make the record-only surface an artifact in the repository rather than a memory.
- Distinguish "we decided not to" from "nobody has yet".
- Prevent the modeled set from drifting into record-only territory without someone
  noticing.

**Non-Goals:**

- Completeness. This is not a list of every unmodeled method, and it must not become one:
  a Bot API bump adds methods, and a list that has to be exhaustive would break on every
  bump.
- Modeling anything. No behavior changes at all.
- Enforcing that deferred clusters ever get built.

## Decisions

### D1. An anti-overlap guard, not a completeness guard

The test asserts `RECORD_ONLY & set(REGISTRY) == set()`. It does **not** assert that every
unmodeled method appears in `RECORD_ONLY`.

This is the whole design decision, and it is the opposite of the completeness guard used
for update triggers. There, exhaustiveness is the point and a new variant *should* break
the build. Here, exhaustiveness would make every Bot API bump a failure for a list that is
documentation, not behavior — and a guard that cries wolf on every bump gets suppressed.

The anti-overlap direction catches the failure that actually matters: someone models
`setPassportDataErrors` without noticing it was a considered exclusion.

### D2. The list lives next to the registry it guards

`RECORD_ONLY` goes in `modeling.py` beside `REGISTRY`, not in the test file. Two reasons:
the guard is then testing the package rather than testing itself, and a contributor adding
a handler sees the exclusion list in the same file, at the moment it is relevant.

### D3. Grouped by reason, not alphabetically

Each group carries why it is excluded, because the reason is the reusable part. "Media
processing is out of scope" answers the next five questions too; a flat list of ninety
method names answers none of them.

### D4. Deferred clusters are named but not enumerated per method

Stars and gifts, sticker sets, stories and business account profile are named as clusters
with a sentence each. Listing their individual methods would duplicate the Bot API and rot;
naming the cluster is enough to answer "is this refused or pending?".

## Risks / Trade-offs

- **The list goes stale after a Bot API bump** → a new method in an excluded family is
  unmodeled and unlisted. Accepted by design (D1): that is the existing default, and the
  guard stays green. The list is documentation with a safety catch, not a contract.
- **It reads as more binding than it is** → someone treats "record-only" as a promise never
  to model. Mitigated by the wording: these are decisions given current demand, and the
  deferred list exists precisely to show the boundary moves.
- **Effort spent on a list nobody reads** → possible. Mitigated by putting the same content
  in the user documentation, where "is `sendGift` modeled?" is a question users actually
  have.

## Migration Plan

None; nothing changes at runtime.

## Open Questions

- Should the docs list be generated from `RECORD_ONLY` rather than hand-written, so the two
  cannot disagree? Attractive, but a Sphinx extension for one list is more machinery than
  the problem deserves. Revisit if they drift.
