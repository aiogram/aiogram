############
sendLocation
############

Use this method to send point on the map. On success, the sent Message is returned.

Returns: :obj:`Message`

.. automodule:: aiogram.api.methods.send_location
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_location(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendLocation`
- :code:`from aiogram.api.methods import SendLocation`
- :code:`from aiogram.api.methods.send_location import SendLocation`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendLocation(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendLocation(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendLocation(...)