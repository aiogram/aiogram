####################
getUserProfileAudios
####################

Returns: :obj:`UserProfileAudios`

.. automodule:: aiogram.methods.get_user_profile_audios
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: UserProfileAudios = await bot.get_user_profile_audios(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_user_profile_audios import GetUserProfileAudios`
- alias: :code:`from aiogram.methods import GetUserProfileAudios`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: UserProfileAudios = await bot(GetUserProfileAudios(...))
