#####################
setMyShortDescription
#####################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_my_short_description
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_my_short_description(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_my_short_description import SetMyShortDescription`
- alias: :code:`from aiogram.methods import SetMyShortDescription`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetMyShortDescription(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetMyShortDescription(...)
