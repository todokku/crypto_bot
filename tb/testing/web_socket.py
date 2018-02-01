import time
import datetime
import pandas as pd
import numpy as np
import asyncio
from stocks.bitfinex.web_socket import WEBSocket as BWS
from testing.logging import Logging

class WEBSocket (BWS):
    _iter_frame = None

    def __init__ (self):
        self.log_info = Logging.log_info
        self.log_error = Logging.log_error

    async def get_data (self):
        try:
            # now = datetime.datetime.now()
        
            # start = int(time.mktime((now - datetime.timedelta (days=1)).timetuple()))
            # end = int(time.mktime(now.timetuple()))

            # query = '''
            #     SELECT * FROM tb.ticker
            #     WHERE tick_time >= toDateTime({start}) AND tick_time <= toDateTime ({end})
            #     ORDER BY tick_time DESC FORMAT CSVWithNames
            #     '''.format (start=start, end=end)
            # self._iter_frame = await self._stock._storage.execute (query)

            # self._iter_frame.to_csv ('day.csv', index=True)

            self._iter_frame = pd.read_csv ('testing/day.csv', dtype={'close':np.float64})

            self._iter_frame.loc[:, 'tick_time'] = pd.to_datetime(self._iter_frame.loc[:, 'tick_time'])
            self._iter_frame['timestamp'] = self._iter_frame.loc[:, 'tick_time'].apply (lambda tick_time: time.mktime (tick_time.timetuple()))
            self._iter_frame = self._iter_frame.set_index (pd.to_datetime(self._iter_frame.loc[:, 'tick_time']).values)
            self._iter_frame = self._iter_frame.iloc[::-1]

            self.log_info (self._iter_frame.iloc[0].name)
            self.log_info (self._iter_frame.iloc[self._iter_frame.shape[0]-1].name)

            # pre_frame = self._iter_frame.loc[:self._iter_frame.iloc[0].name + datetime.timedelta(minutes=30)]
            # self._iter_frame = self._iter_frame.iloc[:pre_frame.shape[0]]
        except Exception as e:
            self.log_error (e)

    async def listen (self):
        try:
            await self.get_data ()
            current_idx = 0
            for idx, tick in self._iter_frame.iterrows():
                if current_idx % int(self._iter_frame.shape[0] / 100) == 0:
                    self.log_info (current_idx // int(self._iter_frame.shape[0] / 100))
                if len (self._tick_actions) > 0:
                    for tick_action in self._tick_actions:
                        await tick_action (tb_tick)
                await asyncio.sleep (0)
                current_idx += 1
        except Exception as e:
            self.log_error (e)