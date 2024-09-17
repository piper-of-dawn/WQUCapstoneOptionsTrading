import pickle
import aiohttp
import asyncio
from rich import print
import polars as pl
import os
from tqdm import tqdm
from functools import reduce

async def get_expirations (session, ticker):
    print(f"Fetching expirations for {ticker}...")
    base_url = "http://127.0.0.1:25510/v2/list/expirations"
    params = {
        'root': ticker
    }
    try:
        async with session.get(base_url, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            print(f"Fetched expirations for {ticker}")
            return {ticker: data}
    except Exception as e:
        print(f"Error fetching expirations for {ticker}: {e}")
        return {ticker: None}
    

async def fetch_stock_data(session, ticker, start_date, end_date, interval_size):
    print(f"Fetching data for {ticker}...")
    base_url = "http://127.0.0.1:25510/v2/hist/stock/quote"
    params = {
        'root': ticker,
        'start_date': start_date,
        'end_date': end_date,
        'ivl': interval_size
    }

    try:
        # Send GET request asynchronously
        async with session.get(base_url, params=params) as response:
            response.raise_for_status()
            # Parse JSON response
            data = await response.json()
            print(f"Fetched data for {ticker}")
            return {ticker: data}
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return {ticker: None}
    
async def fetch_multiple(session, fetch_function, items, *args, **kwargs):
    tasks = [fetch_function(session, item, *args, **kwargs) for item in items]
    results = await asyncio.gather(*tasks)
    return results

def get_data_for_items(fetch_function, items, *args, **kwargs):
    # Run the event loop for asynchronous execution
    return asyncio.run(fetch_multiple(fetch_function, items, *args, **kwargs))


async def fetch_multiple_tickers(tickers, start_date, end_date, interval_size, tasks):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_stock_data(session, ticker, start_date, end_date, interval_size) for ticker in tickers]
        results = await asyncio.gather(*tasks)
        return results

def get_stock_data_for_tickers(tickers, start_date, end_date, interval_size):
    # Run the event loop for asynchronous execution
    return asyncio.run(fetch_multiple_tickers(tickers, start_date, end_date, interval_size))


tickers = pl.read_csv('tickersAndIndustries.csv')['Ticker'].to_list()
start_date = "20190902"
end_date = "20240910"
interval_size = 60000

n = 5
for i in range(0, len(tickers), n):
    print(i)
    data = get_stock_data_for_tickers(tickers[i:i+n], start_date, end_date, interval_size)
    with open(f'price{i}.pkl', 'wb') as f:
        pickle.dump(data, f)
    print(f"{i} epoch done")


price_data = [f for f in os.listdir() if f.startswith('price')]

pkl_file = price_data[0]
with open(pkl_file, 'rb') as f:
        data = pickle.load(f)  
schema=data[0]['WEAT']['header']['format']




def make_df(pkl_file, schema):
    with open(pkl_file, 'rb') as f:
        data = pickle.load(f)    
    ticker_list = [list(d.keys())[0] for d  in data]
    data_list = [pl.DataFrame(d[t]['response'], schema=schema, orient='row').with_columns(pl.lit(t).alias('ticker')) for d, t in zip(data, ticker_list)]
    return reduce(lambda x, y: pl.concat([x, y]), data_list)

big_list = [make_df(f, schema) for f in tqdm(price_data)]
DATA = reduce(lambda x, y: pl.concat([x, y]), big_list)
DATA.write_parquet('price_data.parquet')
