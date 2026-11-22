.. _tracing:

=======
Tracing
=======

One trace hook is shared by the testing toolkit, OpenTelemetry and logging.
A tracer opens one synchronous span per dispatch stage.

.. note::

    This page describes the interface only. Installing tracers on the dispatcher
    is not wired yet.


Protocol
========

A tracer is any object with a :code:`span` method that returns a context manager.
The context manager yields a :class:`~aiogram.dispatcher.tracing.Span` or :code:`None`.

.. code-block:: python

    from contextlib import contextmanager
    from typing import Any, Iterator

    from aiogram.dispatcher import SpanKind


    class PrintSpan:
        def set_attribute(self, key: str, value: Any) -> None:
            print("  ", key, "=", value)


    class PrintTracer:
        @contextmanager
        def span(self, kind: SpanKind, **attrs: Any) -> Iterator[PrintSpan]:
            print("enter", kind, attrs)
            try:
                yield PrintSpan()
            finally:
                print("exit", kind)

.. autoclass:: aiogram.dispatcher.tracing.SpanKind
    :members:
    :undoc-members:

.. autoclass:: aiogram.dispatcher.tracing.Span
    :members:

.. autoclass:: aiogram.dispatcher.tracing.DispatchTracer
    :members:


Calling rules
=============

aiogram calls tracers by hand instead of with :code:`with` statements,
so a tracer can never change what the application sees:

1. Tracers are entered in order. If :code:`span()` or :code:`__enter__()` raises, the error
   is logged on :code:`aiogram.dispatcher` and that tracer is skipped for the stage.
   It is never exited.
2. The stage runs.
3. Each span that is not :code:`None` gets a :code:`result` or an :code:`exception` attribute.
   A failing :code:`set_attribute` is logged and ignored.
4. Tracers are exited in reverse order. The return value of :code:`__exit__` is ignored,
   so a tracer cannot suppress an error. A raising :code:`__exit__` is logged and the other
   tracers are still exited.
5. The stage result is returned, or the original exception is re-raised as the same object,
   including :code:`asyncio.CancelledError`.

Every tracer failure writes one log record with a traceback.
Tracer state is shared between threads: making a tracer thread-safe is up to its author.


Attributes
==========

========================= ===========================================================
Key                       Meaning
========================= ===========================================================
:code:`update_id`         Update identifier
:code:`update_type`       Update type, e.g. :code:`message`
:code:`bot_id`            Bot identifier
:code:`router`            Router name
:code:`handler`           Handler name
:code:`middleware`        Middleware name
:code:`filter`            Filter name
:code:`method`            Bot API method name (:code:`API_CALL` spans)
:code:`phase`             Sub-phase of a span, e.g. :code:`decode` on :code:`UPDATE`
:code:`isolation_wait_ms` Time spent waiting for the isolation lock (:code:`UPDATE`)
:code:`result`            :code:`unhandled`, :code:`skip` or the result's type name
:code:`exception`         The exception object raised by the stage
========================= ===========================================================

New span kinds and keys can be added in a minor release.


Callback tracer
===============

:class:`~aiogram.dispatcher.tracing.CallbackTracer` turns two callbacks into a tracer:

.. code-block:: python

    from aiogram.dispatcher import CallbackTracer


    def on_exit(kind, attrs, result, exception):
        print(kind, attrs.get("handler"), result or repr(exception))


    tracer = CallbackTracer(on_exit=on_exit)

.. autoclass:: aiogram.dispatcher.tracing.CallbackTracer
