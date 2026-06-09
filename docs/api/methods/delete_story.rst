###########
deleteStory
###########

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_story
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_story(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_story import DeleteStory`
- alias: :code:`from aiogram.methods import DeleteStory`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteStory(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteStory(...)
