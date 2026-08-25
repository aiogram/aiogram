from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from aiogram import methods
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError
from aiogram.methods import TelegramMethod

from .mounting import detached_copy

if TYPE_CHECKING:
    from collections.abc import Callable

    from aiogram.client.bot import Bot

#: What Telegram answers when the addressee has blocked the bot. Declared here so
#: :meth:`aiogram.test.BotTestEnvironment.blocked` and a test asserting on the string a
#: real bot would see agree by construction.
BLOCKED_BY_USER = "Forbidden: bot was blocked by the user"

#: Name prefixes of the methods that deliver something *into* a chat, and therefore of the
#: methods a block stops. Matching by prefix rather than listing thirty classes is what
#: keeps the set correct across a Bot API bump: ``sendChecklist`` and ``sendPaidMedia``
#: joined the API long after this toolkit was written, and a hand-kept list would have
#: quietly stopped covering them. The ``chat_id`` requirement is what excludes the odd
#: one out — ``sendChatJoinRequestWebApp`` addresses a web-app query, not a chat.
_DELIVERY_PREFIXES = ("Send", "Copy", "Forward")

#: Every method that delivers content into a chat named by ``chat_id``.
DELIVERY_METHODS: tuple[type[TelegramMethod[Any]], ...] = tuple(
    sorted(
        (
            member
            for member in vars(methods).values()
            if isinstance(member, type)
            and issubclass(member, TelegramMethod)
            and member.__name__.startswith(_DELIVERY_PREFIXES)
            and "chat_id" in member.model_fields
        ),
        key=lambda item: item.__name__,
    ),
)

#: Distinguishes "the method has no such field" from "the field is None".
_MISSING = object()


@dataclass
class Outcome:
    """A declared answer for a method: either a result or an error."""

    result: Any = None
    error: type[TelegramAPIError] | TelegramAPIError | None = None
    message: str = "Bad Request: test error"
    remaining: int | None = None

    def consume(self) -> None:
        if self.remaining is not None:
            self.remaining -= 1

    @property
    def exhausted(self) -> bool:
        return self.remaining is not None and self.remaining <= 0

    def apply(self, method: TelegramMethod[Any], bot: Bot | None = None) -> Any:
        """
        The declared answer, as a fresh object bound to whoever asked for it.

        The declared object belongs to the test — it is often built once at module level
        and reused — while the answer belongs to the caller: it gets mounted to the calling
        bot, and a modeled follow-up may edit it. Handing out the very object the test
        declared would mean the test's own object is mutated by the call it describes, and
        that it holds a reference to every :class:`~aiogram.client.bot.Bot` that ever
        received it, long after those environments were disposed. Copying also makes a
        repeated override (``times=None``) behave like the API it stands in for: each call
        gets its own response.

        The caller's bot is known here, so the copy is bound as it is made and the session's
        own :func:`~aiogram.test.mounting.mount` prunes at its root — one walk instead of a
        walk to bind, a walk to unbind, and a walk to bind again.
        """
        if self.error is None:
            return detached_copy(self.result, bot=bot)
        if isinstance(self.error, TelegramAPIError):
            raise self.error
        raise self.error(method=method, message=self.message)


def fresh_result(result: Any) -> Any:
    """
    A copy of a declared result, unbound, the way a real answer is freshly parsed.

    Kept as the name for the unbound half of :meth:`Outcome.apply`; the policy itself lives
    in :func:`aiogram.test.mounting.detached_copy`.
    """
    return detached_copy(result)


@dataclass(frozen=True)
class MethodMatcher:
    """
    Which calls a declared outcome answers.

    An override used to be addressed by method *type* alone, and that is not enough for the
    case it exists for. A bot that reacts to one event by messaging several chats — a game
    engine telling the group and every player at once — makes several ``sendMessage`` calls
    from one trigger, and "make sendMessage fail once" hits whichever of them the engine
    happens to make first. Testing "this one player has blocked the bot" then meant
    reordering the production code so the blocked player is served first, and testing *two*
    blocked players was not expressible at all.

    So an outcome carries the shape of the call it answers: field equalities, AND-ed, plus
    any number of predicates for what equality cannot say. Fields are compared against the
    **resolved** method — the one
    :meth:`aiogram.test.BotTestEnvironment.handle_call` has already filled the bot's
    defaults into — so ``parse_mode=ParseMode.HTML`` matches a call that never mentioned it
    and inherited it from ``Bot(default=...)``, which is the call the API would have seen.
    """

    method_type: type[TelegramMethod[Any]]
    #: Field equalities as pairs rather than a mapping, so a matcher stays frozen and a
    #: builder can snapshot the fields it holds at the moment an outcome is declared.
    fields: tuple[tuple[str, Any], ...] = ()
    predicates: tuple[Callable[[TelegramMethod[Any]], object], ...] = ()

    def matches(self, method: TelegramMethod[Any]) -> bool:
        if not isinstance(method, self.method_type):
            return False
        for name, expected in self.fields:
            if getattr(method, name, _MISSING) != expected:
                return False
        return all(predicate(method) for predicate in self.predicates)

    def describe(self) -> str:
        """How a failure message names the calls this answers."""
        parts = [f"{name}={value!r}" for name, value in self.fields]
        parts.extend(f"where({describe_predicate(predicate)})" for predicate in self.predicates)
        if not parts:
            return self.method_type.__name__
        return f"{self.method_type.__name__}({', '.join(parts)})"


@dataclass(eq=False)
class OverrideRule:
    """One declared answer and the calls it answers, as the registry stores them.

    Compared by identity — ``eq=False`` — because cancelling a handle removes *the* rules
    that handle registered, and two rules declaring the same answer for the same shape are
    a perfectly ordinary thing for a test to do.
    """

    matcher: MethodMatcher
    outcome: Outcome


class OverrideRegistry:
    """
    Per-environment store of declared outcomes, consulted before anything else.

    Rules are kept in one list in registration order rather than bucketed by method type,
    because order across types is now observable: two rules for the same type are tried
    oldest first, and the first whose matcher accepts the call wins.

    **A rule that does not match is not consumed and does not block.** This is the whole
    point of matching: ``take`` walks past a rule addressed to another chat without
    touching its ``times`` budget, so an override declared for one player still answers
    that player's message however many other players were messaged first.
    """

    def __init__(self) -> None:
        self._rules: list[OverrideRule] = []

    def add(self, rule: OverrideRule) -> None:
        self._rules.append(rule)

    def remove(self, rule: OverrideRule) -> None:
        """Take a rule out, if it is still in. Cancelling a spent handle is not an error."""
        for index, candidate in enumerate(self._rules):
            if candidate is rule:
                del self._rules[index]
                return

    @property
    def rules(self) -> list[OverrideRule]:
        """The rules still standing, in the order ``take`` tries them."""
        return list(self._rules)

    def take(self, method: TelegramMethod[Any]) -> Outcome | None:
        for rule in list(self._rules):
            if rule.outcome.exhausted:
                self.remove(rule)
                continue
            if not rule.matcher.matches(method):
                continue
            rule.outcome.consume()
            if rule.outcome.exhausted:
                self.remove(rule)
            return rule.outcome
        return None

    def clear(self) -> None:
        self._rules.clear()


class OverrideHandle:
    """
    What a registration hands back: the way to take it off again.

    Overrides used to be all-or-nothing — ``env.overrides.clear()`` and nothing else — so a
    test that wanted an error to hold for one phase and stop had to either clear every
    override it had declared or express the phase inside the predicate. A handle scopes one
    registration: :meth:`cancel` removes exactly the rules it declared and leaves every
    other rule alone.

    It is also a context manager, which is how the scoped form of
    :meth:`aiogram.test.BotTestEnvironment.blocked` works::

        with env.blocked(chat_id=alice.id):
            await bot_user.send("/start")
        # from here on the bot can message Alice again
    """

    def __init__(self, registry: OverrideRegistry) -> None:
        self._registry = registry
        self._rules: list[OverrideRule] = []

    def register(self, matcher: MethodMatcher, outcome: Outcome) -> OverrideRule:
        """Declare one rule and keep it under this handle's ``cancel``."""
        rule = OverrideRule(matcher=matcher, outcome=outcome)
        self._rules.append(rule)
        self._registry.add(rule)
        return rule

    @property
    def rules(self) -> list[OverrideRule]:
        """The rules this handle declared, whether or not they are still registered."""
        return list(self._rules)

    def cancel(self) -> None:
        """
        Withdraw every rule this handle declared.

        Idempotent, and tolerant of a rule that is already gone — an outcome with a
        ``times`` budget takes itself out of the registry when it is spent, and a handle
        that outlives its own rules is the ordinary case rather than an error. The list of
        what was declared is kept, so a test can still ask.
        """
        for rule in self._rules:
            self._registry.remove(rule)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.cancel()


class OverrideBuilder(OverrideHandle):
    """
    Fluent handle returned by ``environment.on(Method, **field_filters)``.

    ``env.on(SendMessage)`` still answers every ``sendMessage``; the keyword arguments
    narrow it to the calls whose fields are equal to them, AND-ed::

        env.on(SendMessage, chat_id=alice.id).raises(TelegramForbiddenError, times=1)

    :meth:`where` is the escape hatch for what equality cannot express, and both compose:
    the matcher in force when :meth:`returns` or :meth:`raises` is called is the one that
    outcome keeps, so a builder can be narrowed further between two declarations without
    rewriting the first.
    """

    def __init__(
        self,
        registry: OverrideRegistry,
        method_type: type[TelegramMethod[Any]],
        **fields: Any,
    ) -> None:
        super().__init__(registry)
        self._method_type = method_type
        self._fields = _validated_fields(method_type, fields)
        self._predicates: tuple[Callable[[TelegramMethod[Any]], object], ...] = ()

    def where(self, predicate: Callable[[TelegramMethod[Any]], object]) -> OverrideBuilder:
        """
        Narrow this builder by an arbitrary test on the resolved method.

        For everything ``**field_filters`` cannot say — a substring of the text, a keyboard
        with a particular button, a chat id from a set::

            env.on(SendMessage).where(lambda call: "night" in (call.text or "")).raises()

        Several calls AND together, and each applies to the outcomes declared *after* it.
        """
        self._predicates = (*self._predicates, predicate)
        return self

    def matcher(self) -> MethodMatcher:
        """A snapshot of what this builder currently matches."""
        return MethodMatcher(
            method_type=self._method_type,
            fields=tuple(self._fields.items()),
            predicates=self._predicates,
        )

    def returns(self, result: Any, *, times: int | None = None) -> OverrideBuilder:
        self.register(self.matcher(), Outcome(result=result, remaining=times))
        return self

    def raises(
        self,
        error: type[TelegramAPIError] | TelegramAPIError = TelegramBadRequest,
        message: str = "Bad Request: test error",
        *,
        times: int | None = None,
    ) -> OverrideBuilder:
        self.register(
            self.matcher(),
            Outcome(error=error, message=message, remaining=times),
        )
        return self


def block_chat(
    registry: OverrideRegistry,
    chat_id: int,
    message: str = BLOCKED_BY_USER,
) -> OverrideHandle:
    """
    Make every delivery into ``chat_id`` fail the way a block makes it fail.

    One rule per method in :data:`DELIVERY_METHODS`, all under one handle, so the whole
    block is lifted by a single :meth:`OverrideHandle.cancel`. The rules carry no ``times``
    budget: a blocked user stays blocked for as long as the block is in force, and a budget
    would silently un-block them on call *n+1*.
    """
    handle = OverrideHandle(registry)
    for method_type in DELIVERY_METHODS:
        handle.register(
            MethodMatcher(method_type=method_type, fields=(("chat_id", chat_id),)),
            Outcome(error=TelegramForbiddenError, message=message),
        )
    return handle


def describe_predicate(predicate: object) -> str:
    """Best-effort identification of a ``where`` predicate for a failure message."""
    name = getattr(predicate, "__qualname__", None)
    if isinstance(name, str) and name:
        return name
    return repr(predicate)  # pragma: no cover - every callable carries a qualname


def _validated_fields(
    method_type: type[TelegramMethod[Any]],
    fields: dict[str, Any],
) -> dict[str, Any]:
    """
    Reject a filter on a field the method does not have, loudly and immediately.

    A misspelled ``env.on(SendMessage, chat_di=alice.id)`` is the worst possible silent
    failure: the rule is registered, it matches nothing, the override never fires, and the
    test fails much later as "the bot sent the message it was supposed to fail to send".
    Checking the names against the model at registration turns that into a typo report.
    """
    model_fields = method_type.model_fields
    unknown = sorted(name for name in fields if name not in model_fields)
    if unknown:
        known = ", ".join(sorted(model_fields))
        msg = (
            f"{method_type.__name__} has no field(s) {', '.join(unknown)}, so an override "
            f"filtering on them would silently never match.\n"
            f"  known fields: {known}\n"
            f"Use `.where(lambda call: ...)` for anything that is not a field equality."
        )
        raise TypeError(msg)
    return fields
