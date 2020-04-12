# TODO

!!! warning

    Here is lister not all tasks

- [ ] Telegram API features
    - [x] Rewrite Telegram types using **pydantic**
    - [x] Rewrite Telegram methods using **pydantic**
    - [x] Rewrite bot class
    - [ ] Contextual aliases for methods in types
    - [ ] ...
- [ ] Dispatcher features
    - [x] Blueprints/Routers
    - [ ] Refactor FSM
        - [ ] Engine
        - [ ] Builtin storage's
            - [ ] ...
    - [ ] Refactor filters
        - [ ] Engine
        - [ ] Builtin filters
            - [x] Command
            - [x] ContentTypes
            - [x] Text
            - [ ] ...
    - [x] Middlewares
        - [x] Engine
        - [ ] Builtin middlewares
            - [ ] ...
    - [ ] Webhook
    - [ ] Executor
    - [ ] i18n
    - [ ] ...
- [ ] Tests
    - [x] API
        - [x] Sessions
        - [x] Types
        - [x] Methods
        - [x] Client
    - [ ] Dispatcher
        - [x] Dispatcher
        - [x] Router
        - [x] Observers
        - [x] Middleware
        - [ ] Filters
    - [ ] Utils
        - [x] Helper
        - [x] Markdown/HTML
        - [ ] ...
- [ ] CI/CD
    - [ ] Publish to PyPi on tag
    - [x] Build docs on push
    - [x] Code style
        - [x] Test with coverage on pull-request
        - [x] Test with coverage on push
        - [x] mypy on pull-request
        - [x] Flake8 on pull-request
