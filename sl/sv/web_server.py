from aiohttp import web
import asyncio
import jinja2
import aiohttp_jinja2

from routing import routes
from stream_listener import StreamListener
from common import Logger

class WebServer():
    __ip = None
    __port = None
    __app = None
    __stream = None

    def __init__(self):
        self.__ip = '0.0.0.0'
        self.__port = 3000
        self.__app = app = web.Application ()
        self.__stream = StreamListener()

    async def __on_shutdown(self):
        try:
            for ws in self.__app['websockets']:
                await ws.close(code=1001, message='Server shutdown')
        except Exception as e:
            Logger.log_error(e)

    def __configure_app(self):
        aiohttp_jinja2.setup(
                self.__app,
                loader=jinja2.FileSystemLoader('templates'),)

        self.__app['static_root_url'] = '/static'
        self.__app.router.add_static('/static', 'static', name='static')
        for route in routes:
            self.__app.router.add_route(
                    route['method'],
                    route['path'],
                    route['handler'],
                    name=route['name'],)

        self.__app.on_cleanup.append(self.__on_shutdown)
        self.__app['websockets'] = []
        if self.__stream is not None:
            self.__app['stock_stream'] = self.__stream

    async def __ws_run(self):
        runner = web.AppRunner(self.__app)
        await runner.setup()
        site = web.TCPSite(runner, self.__ip, self.__port)
        await site.start()

    def run (self):
        self.__configure_app()
        return asyncio.gather(
               self.__stream.run(),
               self.__ws_run(),)