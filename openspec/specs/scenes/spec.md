# Scenes Specification

## Purpose

Scenes are a higher-level abstraction over the FSM: a class groups the handlers,
enter/leave/exit actions and navigation of one conversational step, removing
manual `set_state` bookkeeping. Scenes build on top of the FSM capability and
require a working storage.

## Requirements

### Requirement: Scene declaration

A scene SHALL be a `Scene` subclass whose state name is taken from the class
`state=` argument (defaulting to `None` when omitted — it is not derived from the
class name), and whose handlers are declared with `@on.<event_type>` decorators.

#### Scenario: Handler declaration

- **GIVEN** `class Quiz(Scene, state="quiz")` with a method decorated `@on.message(F.text)`
- **WHEN** the user is inside the scene and sends text
- **THEN** that method is executed with the usual contextual data

#### Scenario: Entry point

- **WHEN** a handler is decorated with `@on.message.enter()`
- **THEN** it runs when the scene is entered rather than on every message

#### Scenario: Registration

- **WHEN** `SceneRegistry(dispatcher).add(Quiz)` is called, or `Quiz.as_handler()` is registered as a handler
- **THEN** the scene's handlers are wired into the router tree

### Requirement: Scene lifecycle actions

Scenes SHALL support `enter`, `leave` and `exit` actions, invoked automatically
during navigation.

#### Scenario: Enter action

- **WHEN** a scene is entered
- **THEN** its `enter` action runs after the FSM state is switched to the scene state

#### Scenario: Leave action

- **WHEN** navigation moves away from the scene
- **THEN** its `leave` action runs before the next scene is entered

#### Scenario: Exit action

- **WHEN** the scene stack is exited entirely
- **THEN** the `exit` action runs and the FSM state is cleared

### Requirement: Wizard navigation

Scene handlers are methods on the scene instance and SHALL reach a `SceneWizard`
through `self.wizard` to navigate. Contextual data separately carries a
`ScenesManager` under the `scenes` key for entering scenes from ordinary handlers.

#### Scenario: Wizard access

- **WHEN** a scene handler method runs
- **THEN** `self.wizard` is a `SceneWizard` bound to the current scene, state and event

#### Scenario: Entering from outside a scene

- **WHEN** a plain handler declares a `scenes` argument
- **THEN** a `ScenesManager` is injected and `await scenes.enter(Quiz)` starts the scene

#### Scenario: Going to another scene

- **WHEN** `await self.wizard.goto(Other)` is called
- **THEN** the current scene leaves and `Other` is entered

#### Scenario: Retake

- **WHEN** `await self.wizard.retake()` is called
- **THEN** the current scene is re-entered, re-running its enter action

#### Scenario: Back

- **WHEN** `await self.wizard.back()` is called
- **THEN** the previous scene from the history is entered

#### Scenario: Exit

- **WHEN** `await self.wizard.exit()` is called
- **THEN** the scene stack is exited and the state cleared

#### Scenario: Declarative transitions

- **WHEN** a handler is decorated with `@on.message(F.text, after=After.goto(Other))`
- **THEN** the transition happens automatically after the handler returns

### Requirement: Scene history

The scene machinery SHALL maintain a bounded per-user navigation history in a
separate storage destiny, enabling `back()` and rollback.

#### Scenario: History growth

- **WHEN** the user moves through several scenes
- **THEN** each transition is pushed to the history, capped at the configured size

#### Scenario: History reset

- **GIVEN** a scene declared with `reset_history_on_enter=True`
- **WHEN** it is entered
- **THEN** the accumulated history is cleared

### Requirement: Scene configuration

Scene behavior SHALL be configurable per class and inherited by subclasses.

#### Scenario: Data reset

- **GIVEN** `reset_data_on_enter=True`
- **WHEN** the scene is entered
- **THEN** the FSM data is cleared

#### Scenario: Stateless callback queries

- **GIVEN** `callback_query_without_state=True`
- **WHEN** a callback query arrives while the user has no state
- **THEN** the scene's callback query handlers are still eligible

#### Scenario: Inheritance

- **WHEN** a scene subclasses another scene without repeating configuration
- **THEN** the parent's configuration values are inherited
