######################
declineChatJoinRequest
######################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.decline_chat_join_request
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.decline_chat_join_request(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.decline_chat_join_request import DeclineChatJoinRequest`
- alias: :code:`from aiogram.methods import DeclineChatJoinRequest`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeclineChatJoinRequest(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeclineChatJoinRequest(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.decline`
