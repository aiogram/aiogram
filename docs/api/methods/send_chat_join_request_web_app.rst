#########################
sendChatJoinRequestWebApp
#########################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.send_chat_join_request_web_app
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.send_chat_join_request_web_app(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_chat_join_request_web_app import SendChatJoinRequestWebApp`
- alias: :code:`from aiogram.methods import SendChatJoinRequestWebApp`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SendChatJoinRequestWebApp(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendChatJoinRequestWebApp(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.send_webapp`
