# Tasks

## 1. Declared refusals

- [x] 1.1 Declare every refusal in `aiogram.test.refusals`, sourced or best-effort, and raise them from the sites (design D1); verify no `ApiRejection` is built from a literal
- [x] 1.2 Guarantee the codes and the sourced texts bots match on (design D2, D3); verify each code becomes its exception type and the documentation lists the guaranteed texts

## 2. Topic rights

- [x] 2.1 Check the rights before an unknown topic is looked up (design D4); verify a plain-member bot is refused for the right and one holding it meets `message thread not found`

## 3. Tests and docs

- [x] 3.1 Match a description in the toolkit's tests only for a guaranteed text, and document the contract in `docs/dispatcher/testing.rst`

## 4. Integration

- [x] 4.1 Run `make lint`, `uv run pytest tests` with `aiogram/test` at 100% coverage, the docs build and `openspec validate --all --strict`; verify all pass with no new warnings
