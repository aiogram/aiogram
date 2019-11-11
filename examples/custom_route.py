import logging
from aiohttp import web
import typing

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.webhook import WebhookRequestHandler
from aiogram.utils.executor import Executor
from loguru import logger


API_TOKEN = 'BOT TOKEN'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\nI'm Custom Route Example bot!\nPowered by aiogram.\nSend any request to /ping route")


@dp.message_handler()
async def echo(message: types.Message):
    await message.reply(message.text, reply=False)



async def ping(request: web.Request):
    '''
        ping pong beep
    '''
    return web.Response(text="I`m ok!")

async def who_am_i(request: web.Request):
    '''
        Return bot info from this route
    '''
    me = await request.app['BOT_DISPATCHER'].bot.me
    return web.json_response(me.as_json())



class CustomExecutor(Executor):
    '''
        first way for add custom route to your bot is
        inherit from Executor class and overwrite run_app
        method so you can easily add own routes
    '''
    def run_app(self, port: int = 8080, **kwargs,):
        web.run_app(self._web_app, **kwargs, port = port)
    
    def add_subapp(self, subapp: web.Application, subapp_prefix: str):
        self._web_app.add_subapp(subapp_prefix, subapp)
    
    def add_routes(self, *routes: typing.List[web.RouteDef]):
        self._web_app.add_routes(*routes)
    
    def add_route(self, route: web.RouteDef):
        self.add_routes([route])

if __name__ == '__main__':
    #App which realize custom HTTP API methods
    custom_app = web.Application()
    custom_app.add_routes([web.get('/ping', ping)])

    #executor for our bot. Here we add Dispatcher and other bot-need stuff
    executor = CustomExecutor(dp, skip_updates = True, check_ip=False)
    executor.set_webhook(webhook_path='/bot')

    #interesting!
    executor.add_subapp(custom_app, '/healthchek')

    #more interest!
    executor.add_routes([web.get('/me', who_am_i)])
    executor.add_route(web.get('/ping', ping))

    #start global blocking app
    executor.run_app()
