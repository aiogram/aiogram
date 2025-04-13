##################
convertGiftToStars
##################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.convert_gift_to_stars
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.convert_gift_to_stars(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.convert_gift_to_stars import ConvertGiftToStars`
- alias: :code:`from aiogram.methods import ConvertGiftToStars`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(ConvertGiftToStars(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return ConvertGiftToStars(...)
