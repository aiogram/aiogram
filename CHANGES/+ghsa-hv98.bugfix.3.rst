The "Detected unknown update type" warning no longer includes the update, so Python's warning registry no longer keeps a copy of every such update; the update is logged on :code:`aiogram.event` at :code:`DEBUG`.
Reported by the Anthropic OSS Scanner (ANT-2026-PI9G2NGU).
