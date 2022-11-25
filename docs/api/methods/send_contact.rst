###########
sendContact
###########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_contact
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_contact(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_contact import SendContact`
- alias: :code:`from aiogram.methods import SendContact`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendContact(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendContact(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_contact`
- :meth:`aiogram.types.message.Message.reply_contact`
