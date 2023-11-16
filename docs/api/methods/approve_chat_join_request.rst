######################
approveChatJoinRequest
######################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.approve_chat_join_request
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.approve_chat_join_request(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.approve_chat_join_request import ApproveChatJoinRequest`
- alias: :code:`from aiogram.methods import ApproveChatJoinRequest`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(ApproveChatJoinRequest(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return ApproveChatJoinRequest(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat_join_request.ChatJoinRequest.approve`
