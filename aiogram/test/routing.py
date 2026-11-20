from __future__ import annotations

from aiogram.dispatcher.router import Router


def detach_router(router: Router) -> Router:
    """
    Allow a router to be included into a dispatcher again.

    A :class:`~aiogram.dispatcher.router.Router` may be attached to one parent for its
    whole lifetime, so a module-level ``router = Router()`` — the dominant real-world
    pattern — can only be included once per process. Tests that build a fresh dispatcher
    per test hit ``RuntimeError: Router is already attached`` on the second test; calling
    this first makes the router reusable.
    """
    router._parent_router = None
    return router
