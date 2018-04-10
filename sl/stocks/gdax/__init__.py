from common import Logger
from stocks.gdax.socket import Socket

class GDAX ():
    __socket = None
    __stream = None

    def __init__ (self, stream=None):
        self.__socket = Socket ()
        self.__stream = stream

    async def run(self):
        async for tick in self.__socket.run():
            if self.__stream is not None:
                await self.__stream.publish(tick)
