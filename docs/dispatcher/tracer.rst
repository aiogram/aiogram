######
Tracer
######

This module provides the ``AbstractTracer`` class which is used for telemetry and performance monitoring in aiogram.

Standard flow
=============

Each manager getter has the signature ``(target_object: Any) -> AbstractAsyncContextManager[None] | None``.
So, if the tracer is set, framework will get context manager from corresponding method,
and use it to wrap the execution of the corresponding component. If the manager returns ``None``,
tracing for this component will be skipped.

Notice: for handlers registered with multiple uncorrelated filters, e.g.


.. code-block:: python

  @dp.message(F.text == "1")
  @dp.message(F.caption == "1")
  async def handler(message: Message):
    pass


filter manager will be obtained via ``get_filter_span_manager`` and opened as many times
as the observer(``dp.message``) called (twice in this example) but the argument is the same ``HandlerObject`` during all calls.


.. note::
  If an exception is raised during any interaction with the tracer, it will be suppressed and logged automatically
  without interrupting the normal flow of the application.

.. data:: SPAN_MANAGER_TYPE
   :annotation: = AbstractAsyncContextManager[None] | None

.. autoclass:: aiogram.tracer.AbstractTracer
    :members: get_middleware_span_manager, get_filter_span_manager, get_handler_span_manager, get_trigger_span_manager

Example of implementation
-------------------------

.. code-block:: python

  import contextlib

  from aiogram import Dispatcher
  from aiogram.tracer import AbstractTracer
  from aiogram.types import TelegramObject


  class MySimpleTracer(AbstractTracer):
      def get_handler_span_manager(self, handler): return None

      def get_filter_span_manager(self, handler): return None

      def get_middleware_span_manager(self, middleware): return None

      @contextlib.asynccontextmanager
      async def get_trigger_span_manager(self, event: TelegramObject):
          print(f"Start processing update, type: {type(event).__name__}")
          yield
          print(f"End processing update, type: {type(event).__name__}")

  dp = Dispatcher(tracer=MySimpleTracer())
