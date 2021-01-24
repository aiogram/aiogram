####################
getUserProfilePhotos
####################

Returns: :obj:`UserProfilePhotos`

.. automodule:: aiogram.methods.get_user_profile_photos
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: UserProfilePhotos = await bot.get_user_profile_photos(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_user_profile_photos import GetUserProfilePhotos`
- alias: :code:`from aiogram.methods import GetUserProfilePhotos`

In handlers with current bot
----------------------------

.. code-block:: python

    result: UserProfilePhotos = await GetUserProfilePhotos(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: UserProfilePhotos = await bot(GetUserProfilePhotos(...))

