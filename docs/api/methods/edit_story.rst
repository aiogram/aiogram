#########
editStory
#########

Returns: :obj:`Story`

.. automodule:: aiogram.methods.edit_story
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Story = await bot.edit_story(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_story import EditStory`
- alias: :code:`from aiogram.methods import EditStory`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Story = await bot(EditStory(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditStory(...)
