from aiogram.dispatcher.middlewares import BaseMiddleware


class EnvironmentMiddleware(BaseMiddleware):
    def __init__(self, context=None):
        super(EnvironmentMiddleware, self).__init__()

        if context is None:
            context = {}
        self.context = context

    def update_data(self, data):
        dp = self.manager.dispatcher
        data.update(
            bot=dp.bot,
            dispatcher=dp,
            loop=dp.loop
        )
        if self.context:
            data.update(self.context)

    async def trigger(self, action, args):
        if 'error' not in action and action.startswith('pre_process_'):
            self.update_data(args[-1])
            return True
