"""
Token-absence check for exceptions, shared by every test that proves aiogram never builds
token-bearing text (network errors, log records, cancellation paths).

Usage::

    from tests.token_safety import FAKE_TOKEN, assert_token_absent

    async with Bot(FAKE_TOKEN).context() as bot:
        with pytest.raises(TelegramNetworkError) as exc_info:
            await bot.get_me()
    assert_token_absent(exc_info.value)

The check covers what a user or an error tracker sees: ``str()``, ``repr()``, the formatted
traceback and every exception of the chain they walk (``__cause__``, else ``__context__``
unless ``__suppress_context__`` is set, as ``traceback`` and error trackers do). It does not
look at attributes such as ``TelegramNetworkError.original``, nor at a suppressed
``__context__``: both hold the raw error by design, assert on them separately.
"""

import traceback

# Shaped like a real token: a numeric bot id, then a 35-character secret
FAKE_TOKEN = "123456:" + "A" * 35


def assert_token_absent(exc: BaseException, token: str = FAKE_TOKEN) -> None:
    """
    Fail if the secret part of ``token`` appears in the text of ``exc`` or of any
    exception chained to it.

    Only the part after ``:`` is searched for: the redacted form ``<bot id>:***`` keeps
    the bot id on purpose.
    """
    secret = token.partition(":")[2]
    assert secret, f"token {token!r} has no secret part"
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        for text in (
            str(current),
            repr(current),
            "".join(traceback.format_exception(current)),
        ):
            assert secret not in text, f"token found in {type(current).__name__}: {text}"
        current = current.__cause__ or (
            None if current.__suppress_context__ else current.__context__
        )
