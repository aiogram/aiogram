#########
sendAudio
#########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_audio
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_audio(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_audio import SendAudio`
- alias: :code:`from aiogram.methods import SendAudio`

In handlers with current bot
----------------------------

.. code-block:: python

    result: Message = await SendAudio(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendAudio(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendAudio(...)
