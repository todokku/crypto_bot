import datetime
import asyncio
import pandas as pd

from common import utils
from common import Logger
from common import decorators

class Connection():
    __source = None
    __recipient = None
    __filter = None

    __buffer_size = None
    __buffer = None
    __last_request = None

    def __init__(self,
            source=None, recipient=None, fltr=None, buffer_size=None):
        self.__source = source
        self.__recipient = recipient
        self.__filter = fltr or pd.Series()

        self.__buffer_size = buffer_size or datetime.timedelta(seconds=0)
        self.__buffer = pd.DataFrame()
        self.__last_request = datetime.datetime.now()

    async def __send(self, message):
        try:
            if isinstance(message, pd.DataFrame):
                Logger.log_info(message)
            if (self.__filter is None
                    or self.__compare_with_filter(message)):
                current_time = datetime.datetime.now()
                message.name = current_time
                self.__buffer = self.__buffer.append(message)

                if current_time - self.__last_request >= self.__buffer_size:
                    await self.__release_buffer()

                await asyncio.sleep(1
                        - (current_time - self.__last_request).total_seconds())
                current_time = datetime.datetime.now()
                if (current_time - self.__last_request >= self.__buffer_size
                        and self.__buffer.shape[0] > 0):
                    await self.__release_buffer()

        except Exception as e:
            Logger.log_error(e)

    async def __release_buffer(self):
        try:
            current_time = datetime.datetime.now()
            data = self.__buffer.loc[
                    self.__last_request:current_time, :]

            self.__last_request = current_time
            await self.__recipient.send(utils.stringify_data(data))
            self.__buffer = self.__buffer.loc[current_time:, :]
        except Exception as e:
            Logger.log_error(e)


    def __compare_with_filter(self, message):
        if self.__filter.empty:
            return False

        for item in self.__filter.index:
            if (item not in message.index
                    or message.at[item] not in self.__filter.at[item]):
                return False

        return True

################################   API   #####################################

    async def send(self, message):
        try:
            Logger.log_info(isinstance(message, pd.DataFrame))
            await self.__send(message)
        except Exception as e:
            Logger.log_error(e)

    def set_filter(self, fltr):
        Logger.log_info(fltr)
        self.__filter = fltr

    def add_filter(self, fltr):
        for item in fltr.index:
            if item in self.__filter.index:
                if isinstance(fltr.at[item], (list, set,)):
                    self.__filter.at[item] = (self.__filter.at[item]
                            + list(fltr.at[item]))
                else:
                    self.__filter.at[item] = self.__filter.at[item].append(
                            fltr.at[item])
            else:
                if isnstance(fltr.at[item], (list, set,)):
                    self.__filter.at[item] = list(fltr.at[item])
                else:
                    self.__filter.at[item] = [fltr.at[item]]
