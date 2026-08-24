## MODIFIED Requirements

### Requirement: Unmodeled methods are recorded and answered

Any Bot API method the environment does not model SHALL still succeed by default: the
call is recorded and answered with a schema-valid result synthesized from the method's
declared return type. Synthesis SHALL derive from the generated method and type metadata,
so newly added Bot API methods work without changes to the toolkit.

The set of methods that are deliberately left unmodeled SHALL be enumerated rather than
implied, and SHALL distinguish surfaces that are record-only by decision from clusters
whose modeling is merely deferred.

#### Scenario: A method with no state semantics returns a valid object

- **WHEN** a handler calls a method the environment does not model and whose return type
  is a Bot API object
- **THEN** the call returns an instance of that type with all required fields populated,
  and the call is visible in the call log

#### Scenario: A newly added Bot API method needs no toolkit change

- **WHEN** the framework gains a new generated method and a handler calls it
- **THEN** the call succeeds with a synthesized result without any update to the testing
  package

#### Scenario: A record-only method is never also modeled

- **WHEN** the enumerated record-only surface is compared against the modeled method
  registry
- **THEN** the two do not overlap, so modeling one of those methods requires removing it
  from the record-only list in the same change

## ADDED Requirements

### Requirement: The record-only surface is an enumerated decision

The toolkit SHALL name the Bot API surfaces it does not model and does not intend to,
together with the reason each is excluded: nothing a test reads back, media processing, or
a layer the toolkit deliberately does not drive. Clusters whose modeling is deferred rather
than refused SHALL be listed separately, so "not yet" is distinguishable from "no".

#### Scenario: A contributor can tell refusal from deferral

- **WHEN** someone asks whether a given unmodeled method should be modeled
- **THEN** the answer is readable from the enumerated lists rather than inferred from the
  absence of an implementation

#### Scenario: The documentation shows the same boundary

- **WHEN** a user looks for a method in the documentation
- **THEN** they can see whether it is modeled, deliberately record-only, or a deferred
  candidate
