# Internationalization Specification

## Purpose

`aiogram.utils.i18n` provides gettext-based translations with per-update locale
resolution, so handlers can call `gettext(...)` without threading a locale
through the call stack.

## Requirements

### Requirement: Translation core

`I18n` SHALL load compiled gettext catalogs from a directory and expose
`gettext` / `ngettext` lookups with a configurable default locale and domain.

#### Scenario: Loading catalogs

- **GIVEN** `I18n(path="locales", default_locale="en", domain="messages")`
- **WHEN** available locales are queried
- **THEN** every locale directory containing a compiled catalog is listed

#### Scenario: Missing translation

- **WHEN** a message id has no translation in the current locale
- **THEN** the original string is returned instead of raising

#### Scenario: Plurals

- **WHEN** `ngettext(singular, plural, n)` is used
- **THEN** the plural form is chosen according to the target locale's rules

### Requirement: Context-bound translation functions

Module-level `gettext`, `ngettext` and their lazy variants SHALL resolve against
the locale that is active in the current context.

#### Scenario: Inside a handler

- **WHEN** `gettext("hello")` (commonly aliased `_`) is called inside a handler
- **THEN** the translation for that update's locale is returned

#### Scenario: Outside a context

- **WHEN** a context-bound function is called with no active `I18n` context
- **THEN** a `LookupError` is raised

#### Scenario: Lazy translation

- **WHEN** `lazy_gettext(...)` is used at import time, e.g. in a keyboard definition
- **THEN** the string is resolved at render time using the then-current locale

#### Scenario: Manual context

- **WHEN** `with i18n.context(): i18n.current_locale = "de"` is used
- **THEN** translations inside the block use `de`

### Requirement: Locale resolution middlewares

The framework SHALL provide middlewares that set the active locale per update.

#### Scenario: From the user

- **GIVEN** `SimpleI18nMiddleware`
- **WHEN** an update arrives from a user with `language_code="uk"` and that locale exists
- **THEN** `uk` is used, otherwise the default locale

#### Scenario: Fixed locale

- **GIVEN** `ConstI18nMiddleware("fr", i18n)`
- **THEN** every update is handled with `fr`

#### Scenario: User-selected locale

- **GIVEN** `FSMI18nMiddleware`
- **WHEN** `await middleware.set_locale(state, "de")` has been called for a user
- **THEN** their subsequent updates use `de`, persisted in FSM data across restarts

#### Scenario: Custom resolution

- **WHEN** `I18nMiddleware` is subclassed and `get_locale` overridden
- **THEN** the returned locale is used for the update

### Requirement: Contextual data exposure

The active `I18n` instance and the middleware itself SHALL be available to
handlers under configurable keys. The resolved locale is not placed in
contextual data — it is carried in the context and read via `i18n.current_locale`.

#### Scenario: Handler access

- **WHEN** a handler declares an `i18n` argument
- **THEN** the active `I18n` instance is injected (key configurable via `i18n_key`)

#### Scenario: Middleware access

- **WHEN** a handler declares an `i18n_middleware` argument
- **THEN** the middleware instance is injected, so e.g. `FSMI18nMiddleware.set_locale` can be called from a handler
