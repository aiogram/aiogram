###########
sendContact
###########

Use this method to send phone contacts. On success, the sent Message is returned.

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_contact
    :members:
    :member-order: bysource
    :special-members: __init__
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

- :code:`from aiogram.methods import SendContact`
- :code:`from aiogram.methods import SendContact`
- :code:`from aiogram.methods.send_contact import SendContact`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendContact(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendContact(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendContact(...)