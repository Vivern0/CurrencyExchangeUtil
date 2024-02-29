'''
Allows you to get the exchange rate of the dollar and euro.
Works for the last N days (1-10).
'''
from datetime import datetime, timedelta
import asyncio
import json
import sys
import aiohttp

API_URL = 'https://api.privatbank.ua/p24api/exchange_rates?json&date='
FILENAME = 'currency.json'
CURRENCY_TYPES = ('EUR', 'USD')


class PrettyCurrencyInfo:
    '''Class for normalizing currency data.'''
    def normalyze(self, data: list[dict]) -> list[dict]:
        '''Normalizes the currency data.'''
        res = []
        for elem in data:
            tmp = {}
            date = elem['date']
            exchange_info = elem['exchangeRate']
            for curr in exchange_info:
                if curr['currency'] in CURRENCY_TYPES:
                    tmp[curr['currency']] = {
                        'sale': curr['saleRate'],
                        'purchase': curr['purchaseRate']}
            res.append({date: tmp})
        return res


class CurrencyExchange:
    '''Class for getting exchange rates.'''
    _buffer: dict[str, dict] = {}

    async def exchange_rate(self, days: int) -> list[dict]:
        '''Returns exchange rates for the last days.'''
        date = datetime.now().date()
        dates = [date - timedelta(days=day) for day in range(days)]
        str_dates: list[str] = [date.strftime('%d.%m.%Y') for date in dates]

        res_list = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for str_date in str_dates:
                if str_date in self._buffer:
                    res_list.append(self._buffer[str_date])
                    continue

                task = asyncio.create_task(
                    self.fetch_exchange_rate(session, str_date)
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            for res in results:
                self._buffer[res['date']] = res
                res_list.append(res)

        return res_list

    async def fetch_exchange_rate(
            self,
            session: aiohttp.ClientSession,
            str_date: str) -> dict:
        '''Returns exchange rates for the specified date.'''
        async with session.get(API_URL+str_date) as response:
            res = await response.json()
            return res


def save_to_json(data: list[dict], filename: str) -> None:
    '''Saves data to a JSON file.'''
    with open(filename, 'w', encoding='UTF-8') as fd:
        json.dump(data, fd, indent=4)


if __name__ == '__main__':
    try:
        if len(sys.argv) == 2:
            days_num = int(sys.argv[1])
            if not 1 <= days_num <= 10:
                raise ValueError
        else:
            days_num = 1
    except ValueError:
        print('Error: argument must be number betweeen 1-10')
        sys.exit(1)

    exchanger = CurrencyExchange()
    normalyzer = PrettyCurrencyInfo()

    currency_list = asyncio.run(exchanger.exchange_rate(days_num))
    normalyzed_curr_list = normalyzer.normalyze(currency_list)

    save_to_json(normalyzed_curr_list, FILENAME)

    print(json.dumps(normalyzed_curr_list, indent=2))
