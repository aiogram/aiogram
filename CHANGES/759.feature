Added new custom operation for MagicFilter named :code:`as_`

Now you can use it to get magic filter result as handler argument

.. code-block:: python

    from aiogram import F

    ...

    @router.message(F.text.regexp(r"^(\d+)$").as_("digits"))
    async def any_digits_handler(message: Message, digits: Match[str]):
        await message.answer(html.quote(str(digits)))
