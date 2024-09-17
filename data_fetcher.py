import asyncio
import aiohttp
from rich import print
async def get_expirations(session, ticker):
    print(f"Fetching expirations for {ticker}...")
    base_url = "http://127.0.0.1:25510/v2/list/expirations"
    params = {"root": ticker}
    try:
        async with session.get(base_url, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            print(f"Fetched expirations for {ticker}")
            return {ticker: data}
    except Exception as e:
        print(f"Error fetching expirations for {ticker}: {e}")
        return {ticker: None}


async def fetch_multiple(fetch_function, items, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_function(session, item, *args, **kwargs) for item in items]
        results = await asyncio.gather(*tasks)
        return results


def get_data_for_items(fetch_function, items, *args, **kwargs):
    # Run the event loop for asynchronous execution
    return asyncio.run(fetch_multiple(fetch_function, items, *args, **kwargs))


data = get_data_for_items(get_expirations, ["AAPL", "GOOGL", "MSFT"])
print(data)