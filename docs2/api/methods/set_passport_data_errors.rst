#####################
setPassportDataErrors
#####################

Informs a user that some of the Telegram Passport elements they provided contains errors. The user will not be able to re-submit their Passport to you until the errors are fixed (the contents of the field for which you returned the error must change). Returns True on success.

Use this if the data submitted by the user doesn't satisfy the standards your service requires for any reason. For example, if a birthday date seems invalid, a submitted document is blurry, a scan shows evidence of tampering, etc. Supply some details in the error message to make sure the user knows how to correct the issues.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.set_passport_data_errors
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_passport_data_errors(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SetPassportDataErrors`
- :code:`from aiogram.api.methods import SetPassportDataErrors`
- :code:`from aiogram.api.methods.set_passport_data_errors import SetPassportDataErrors`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await SetPassportDataErrors(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(SetPassportDataErrors(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SetPassportDataErrors(...)