##############
forwardMessage
##############

Use this method to forward messages of any kind. On success, the sent Message is returned.

Returns: :obj:`Message`

.. automodule:: aiogram.api.methods.forward_message
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.forward_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import ForwardMessage`
- :code:`from aiogram.api.methods import ForwardMessage`
- :code:`from aiogram.api.methods.forward_message import ForwardMessage`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await ForwardMessage(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(ForwardMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return ForwardMessage(...)