==============
MessageHandler
==============

There is base class for message handlers.

Simple usage
============

.. code-block:: python

    from aiogram.handlers import MessageHandler

    ...

    @router.message()
    class MyHandler(MessageHandler):
        async def handle(self) -> Any:
            return SendMessage(chat_id=self.chat.id, text="PASS")

Extension
=========

This base handler is subclass of :ref:`BaseHandler <cbh-base-handler>` with some extensions:

- :code:`self.chat` is alias for :code:`self.event.chat`
- :code:`self.from_user` is alias for :code:`self.event.from_user`
