Implemented new filter named :code:`MagicData(magic_data)` that helps to filter event by data from middlewares or other filters

For example your bot is running with argument named :code:`config` that contains the application config then you can filter event by value from this config:

.. code_block: python3

    @router.message(magic_data=F.event.from_user.id == F.config.admin_id)
    ...
