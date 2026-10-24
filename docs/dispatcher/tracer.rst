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

.. note::
  If an exception is raised during any interaction with the tracer, it will be suppressed and logged automatically
  without interrupting the normal flow of the application.

.. data:: SPAN_MANAGER_TYPE
   :annotation: = AbstractAsyncContextManager[None] | None

.. autoclass:: aiogram.tracer.AbstractTracer
    :members: get_middleware_span_manager, get_handler_span_manager, get_trigger_span_manager

Example of implementation
-------------------------

.. code-block:: python

  import contextlib

  from aiogram import Dispatcher
  from aiogram.tracer import AbstractTracer
  from aiogram.types import Update


  class MySimpleTracer(AbstractTracer):
      def get_handler_span_manager(self, handler): return None

      def get_middleware_span_manager(self, middleware): return None

      @contextlib.asynccontextmanager
      async def get_trigger_span_manager(self, update: Update):
          print(f"Start processing update id={update.update_id}")
          yield
          print(f"End processing update id={update.update_id}")

  dp = Dispatcher(tracer=MySimpleTracer())
