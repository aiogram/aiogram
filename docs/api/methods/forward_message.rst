##############
forwardMessage
##############

Returns: :obj:`Message`

.. automodule:: aiogram.methods.forward_message
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.forward_message(...)


As message method
-------------

.. code-block::

    result: Message = await message.forward(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.forward_message import ForwardMessage`
- alias: :code:`from aiogram.methods import ForwardMessage`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(ForwardMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return ForwardMessage(...)
