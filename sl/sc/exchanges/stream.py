import asyncio
import websockets
import datetime

import pandas as pd

from common import formats
from common import utils
from common import Logger
from common import Websocket

from common.abilities import Connectable

from exchanges import all_exchanges

class Stream(Connectable):
    __ip = None
    __port = None
    __connections = None

    __exchanges = None
    __exchanges_connections = None
    price_snapshot = None

    def __init__(self):
        self.__ip = '127.0.0.1'
        self.__port = 8765

        self.__exchanges = [Exchange() for Exchange in all_exchanges]
        self.__exchanges_names = [exchange.name
                for exchange in self.__exchanges]
        self.price_snapshot = pd.DataFrame()

    async def __client_connector(self, pure_websocket, path):
        try:
            websocket = Websocket(pure_websocket)
            connection = self.connect(websocket, tags={'clients'})
            connection.open_channel(name='price_frame')

            await websocket.listen()
            await connection.close()
        except Exception as e:
            Logger.log_error(e)

###########################  API  ############################################
    def run(self):
        tasks = [websockets.serve(
                self.__client_connector, self.__ip, self.__port)]
        for exchange in self.__exchanges:
            task = exchange.run()
            if isinstance(task, list):
                tasks += task
            else:
                tasks.append(task)

            self.connect(exchange, tags={'exchanges', exchange.name})

        return asyncio.gather(*tasks)

    def get_price_snapshot(self):
        return self.price_snapshot

    async def _recieve_message(self, message, connection, channel=None):
        try:
            if 'exchanges' in connection.at['tags'] and channel == 'ticker':
                self.price_snapshot = message.combine_first(
                        self.price_snapshot)
                await self.publish(
                        message,
                        tags={'clients'},
                        channel='price_frame')
        except Exception as e:
            Logger.log_error(e)
