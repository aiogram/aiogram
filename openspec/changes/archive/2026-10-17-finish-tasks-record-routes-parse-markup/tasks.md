# Tasks

## 1. Waiting for background tasks

- [x] 1.1 Add `wait_for_tasks()` over drain's set of tasks, with `BackgroundTaskError` as the base of `DrainedTaskError` (design D1); verify a broadcast finishing, tasks spawned while waiting, failures before and during the wait, the timeout naming coroutines, and a wait from a child task
