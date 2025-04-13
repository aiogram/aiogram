#########
postStory
#########

Returns: :obj:`Story`

.. automodule:: aiogram.methods.post_story
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Story = await bot.post_story(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.post_story import PostStory`
- alias: :code:`from aiogram.methods import PostStory`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Story = await bot(PostStory(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return PostStory(...)
