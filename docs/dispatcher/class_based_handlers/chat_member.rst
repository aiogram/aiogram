=================
ChatMemberHandler
=================

There is base class for chat member updated events.

Simple usage
============

.. code-block:: python

    from aiogram.handlers import ChatMemberHandler

    ...

    @router.chat_member()
    @router.my_chat_member()
    class MyHandler(ChatMemberHandler):
        async def handle(self) -> Any: ...


Extension
=========

This base handler is subclass of :ref:`BaseHandler <cbh-base-handler>` with some extensions:

- :code:`self.chat` is alias for :code:`self.event.chat`
