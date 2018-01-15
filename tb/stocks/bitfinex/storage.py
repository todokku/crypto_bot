import time
import datetime
import pandas as pd

import aiohttp

from abstract.logging import Logging
from stocks.bitfinex.defines import DEFINES

class Storage (Logging):
    def get_sql (self, name):
        with open('./stocks/bitfinex/sql/'+name+'.sql') as f:
            sql = f.read()

        return sql

    def parse_response (self, response):
        response = None if response == '' else response
        if response is not None:
            response = [row.split(',') for row in response.split ('\n')]
            raise Warning ('asd')

        return response

    async def execute (self, query):
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8123/', data=query) as resp:
                text = await resp.text()
                return self.parse_response(text)

    async def insert_ticks (self, ticks):
        try:
            rows = []
            tick_frame = pd.DataFrame (data=[], columns=['timestamp', 'base', 'quot', 'close', 'volume'])
            tick_frame = tick_frame.append (ticks, ignore_index=True)
            
            for idx, tick in tick_frame.iterrows():
                rows.append ('''(toDate({tick_date}), toDateTime{tick_time}, '{base}', '{quot}', {close}, {volume})'''.format (
                    tick_date = int(tick.at['timestamp']),
                    tick_time = int(tick.at['timestamp']),
                    base = str(tick.at['base']),
                    quot = str(tick.at['quot']),
                    close = float(tick.at['close']),
                    volume = float (tick.at['volume'])
                    ))

            query = '''INSERT INTO tb.ticker (tick_date, tick_time, base, quot, close, volume) VALUES {values}'''.format (values=', '.join (rows))
            self.log_info ('Insert to clickhouse request:\n\t{0}\n'.format(str(tick_frame.shape)))
            await self.execute (query)
        except Exception as e:
            self.log_error (e)

    async def get_missing_periods (self, period):
        try:
            missing_periods_sql = self.get_sql ('missing_periods')
            available_data = await self.execute (missing_periods_sql.format(base='btc', quot='usd', start=period['start'], end=period['end'], default_miss_time=DEFINES.MISS_PERIOD))
            periods = []
            if available_data is not None:
                #если последняя доступная дата периода слишком поздняя, то нужно достать все что раньше, до доступной даты минус период тика
                if time.mktime(available_data[0][0].timetuple()) - period['start'] > DEFINES.MISS_PERIOD:
                    periods.append ({
                        'start': period['start'],
                        'end': time.mktime(available_data[0][0].timetuple()) - DEFINES.TICK_PERIOD
                        })

                #посмотрим есть ли пропуски
                for idx in range(2,len(available_data)):
                    periods.append ({
                        'start': time.mktime(available_data[idx][0].timetuple()) - int(available_data[idx][3]) + DEFINES.TICK_PERIOD,
                        'end':time.mktime(available_data[idx][0].timetuple()) - DEFINES.TICK_PERIOD
                        })
                
                if period['end'] - time.mktime(available_data[1][0].timetuple()) > DEFINES.MISS_PERIOD:
                    periods.append ({
                        'start': time.mktime(available_data[1][0].timetuple())+DEFINES.TICK_PERIOD,
                        'end': period['end']
                        })
            else:
                periods.append ({'start': period['start'], 'end': period['end']})

            return periods
        except Exception as e:
            self.log_error (e)