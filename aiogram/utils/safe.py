import typing


async def safe(coro: typing.Coroutine) -> (bool, typing.Any):
    """
    Safety execute coroutine

    Status - returns True if success otherwise False

    :param coro:
    :return: status and result
    """
    try:
        return True, await coro
    except Exception as e:
        return False, e
