import polars as pl
import requests
import pandas as pd
from datetime import timedelta
from functools import lru_cache
from tqdm import tqdm
from itertools import product
from time import time
import concurrent.futures
import diskcache as dc
from loguru import logger
import numpy as np
from toolbox import append_log
debug = logger.debug

cache = dc.Cache('api_cache')

def get_start_and_end_day (ticker):
    quotes_availability = pl.read_parquet('DATA/quote_data_with_min_max_dates.parquet')
    ticker =quotes_availability.filter( (pl.col('ticker').is_in([ticker])))
    start_day = ticker['min_date'][0]
    end_day = ticker['max_date'][0]
    return start_day, end_day



def time_it(func):
    def wrapper(*args, **kwargs):
        start = time()
        result = func(*args, **kwargs)
        end = time()
        print(f"{func.__name__} took {end - start} seconds to execute")
        return result
    return wrapper


@lru_cache(maxsize=128)
def get_available_expirations(ticker):    
    start_day, end_day = get_start_and_end_day(ticker)
    url = f"http://127.0.0.1:25510/v2/list/expirations?root={ticker}"
    api_response = requests.get(url)
    if api_response.status_code != 200:
        append_log(f"Failed to fetch data for {ticker} with status code {api_response.status_code}", level='ERROR', log_file=f'logs/data_fetcher.log')
        append_log(url, level='ERROR', log_file=f'logs/data_fetcher.log')
        return pl.Series(None)
    total_expirations = pl.Series(api_response.json()['response']).cast(pl.String).str.to_date('%Y%m%d')
    expirations_to_study = total_expirations.filter((total_expirations > start_day) & (total_expirations < end_day))    
    contracts1 = pd.date_range(start=start_day,end=expirations_to_study.max(),freq='WOM-3FRI')
    # Saturday following the third friday in every month
    contracts2 = pd.date_range(start=start_day,end=expirations_to_study.max(),freq='WOM-3FRI')+timedelta(days=1)
    # Combine these contracts into a total pandas index list
    contracts = contracts1.append(contracts2)
    contracts = pl.Series(contracts).cast(pl.Date)
    available_expirations = expirations_to_study.filter(expirations_to_study.is_in(contracts))
    append_log(f"Total number of expirations for {ticker}: {len(total_expirations)}", level='INFO', log_file=f'logs/data_fetcher.log')
    append_log(f"Total number of 3rd Fridays and subsequent Saturdays since {start_day}: {len(contracts)}", level='INFO', log_file=f'logs/data_fetcher.log')
    append_log(f"Intersection of number of 3rd Fridays and subsequent Saturdays and expirations available for {ticker} since {start_day}: {len(available_expirations)}", level='INFO', log_file=f'logs/data_fetcher.log')  
    return available_expirations

def get_strike (ticker, expiration, use_cache=False): 
    if use_cache: 
        if ticker in cache:
            append_log(f"Fetching from cache for ticker {ticker}", level='INFO', log_file=f'logs/data_fetcher.log')
            return cache[ticker] 
    api_response = requests.get(f"http://127.0.0.1:25510/v2/list/strikes?root={ticker}&exp={stringify_date(expiration)}")
    if api_response.status_code != 200:
        append_log(f"Failed to fetch data for {ticker} with status code {api_response.status_code}", level='ERROR', log_file=f'logs/data_fetcher.log')
        append_log(f"http://127.0.0.1:25510/v2/list/strikes?root={ticker}&exp={stringify_date(expiration)}", level='ERROR', log_file=f'logs/data_fetcher.log')
        return pl.Series(None)
    strikes = pl.Series(api_response.json()['response'])
    cache.set(ticker, strikes, expire=None)
    return strikes



@lru_cache(maxsize=128)
def get_expiration_and_strike_dict(ticker):
    available_expirations = get_available_expirations(ticker)
    return {exp: get_strike(ticker, exp) for exp in tqdm(available_expirations)}

def get_paired_expirations (ticker):
    available_expirations = get_available_expirations(ticker)
    return pl.DataFrame(zip(available_expirations, available_expirations[1:]), schema=['current', 'next'])

def get_paired_expiration_and_strike (ticker, expiration_day):
    expiration_and_strike_dict = get_expiration_and_strike_dict(ticker)
    paired_expirations = get_paired_expirations(ticker)
    try:
        current, next = list(paired_expirations.filter(pl.col('current')==expiration_day).iter_rows())[0]
    except Exception as e:
        append_log(e, level='ERROR', log_file=f'logs/data_fetcher.log')
        append_log(f"Expiration {expiration_day} is not available for {ticker}", level='ERROR', log_file=f'logs/data_fetcher.log')
        append_log(list(paired_expirations.filter(pl.col('current')==expiration_day).iter_rows()), level='ERROR', log_file=f'logs/data_fetcher.log')
    return list(product([current], [next], expiration_and_strike_dict[current], [ticker]))

def get_paired_expiration_and_strike_for_all_available_expirations (ticker):
    paired_expirations = get_paired_expirations(ticker)
    return [get_paired_expiration_and_strike(ticker, expiration_day) for expiration_day in paired_expirations['current']]

def stringify_date (date):
    return date.strftime('%Y%m%d')

def flatten_list(nested_list):
    return [item for sublist in nested_list for item in sublist]




def fetch (start_expirations_strike):      
    greeks_schema_dict = {
    'ms_of_day': pl.Int64,           # Milliseconds of the day, integer
    'bid': pl.Float64,               # Bid price, float
    'ask': pl.Float64,               # Ask price, float
    'delta': pl.Float64,             # Delta, float
    'theta': pl.Float64,             # Theta, float
    'vega': pl.Float64,              # Vega, float
    'rho': pl.Float64,               # Rho, float
    'epsilon': pl.Float64,           # Epsilon, float
    'lambda': pl.Float64,            # Lambda, float
    'implied_vol': pl.Float64,       # Implied volatility, float
    'iv_error': pl.Float64,          # Implied volatility error, float
    'ms_of_day2': pl.Int64,          # Milliseconds of the day (second instance), integer
    'underlying_price': pl.Float64,  # Underlying asset price, float
    'date': pl.String                  # Date, string
}

    trading_day, expiration, strike, ticker = start_expirations_strike
    trading_day = stringify_date(trading_day)
    expiration = stringify_date(expiration)
    url = f"http://127.0.0.1:25510/v2/hist/option/greeks?root={ticker}&exp={expiration}&strike={strike}&right=C&start_date={trading_day}&end_date={expiration}&ivl=300000"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            
            append_log(f"API returned a status code {response.status_code} for {ticker} with expiration {expiration} for trading day {trading_day}", level='ERROR', log_file=f'logs/data_fetcher.log')
            append_log(f"RogueURL: {url}", level='ERROR', log_file=f'logs/data_fetcher.log')
            df = pl.DataFrame(None, schema=greeks_schema_dict).with_columns([
            pl.lit(expiration).alias('expiration'),
            pl.lit(strike).alias('strike'),
            pl.lit(ticker).alias('ticker'),
            ])
            return df
        else:
            df =pl.DataFrame(response.json()['response'], schema=greeks_schema_dict, orient='row').with_columns([
            pl.lit(expiration).alias('expiration'),
            pl.lit(strike).alias('strike'),
            pl.lit(ticker).alias('ticker'),
        ]) 
    except Exception as e:
        append_log(f"Failed to fetch data for {ticker} with expiration {expiration}  for trading day {trading_day} with error {e}", level='ERROR', log_file=f'logs/data_fetcher.log')
        # Handle empty dataframes (just in case)
        df = pl.DataFrame(None, schema=greeks_schema_dict).with_columns([
            pl.lit(expiration).alias('expiration'),
            pl.lit(strike).alias('strike'),
            pl.lit(ticker).alias('ticker'),
        ]) 
    return df




@lru_cache(maxsize=10)
def get_median_price_dataframe (filename='DATA/median_price_each_day.parquet'):
    return pl.read_parquet(filename)

@lru_cache(maxsize=128)
def get_spot_for_trading_day (ticker, trading_day):
    df = get_median_price_dataframe().filter((pl.col('date') == trading_day) & (pl.col('ticker')==ticker))['weighted_mid_price']
    if (len(df) > 1) :
        raise ValueError(f"Multiple spot prices for trading day {trading_day} for ticker {ticker}")
    if not len(df):
        raise ValueError(f"No spot price for trading day {trading_day} for ticker {ticker}")
    return df.item()
    
def find_nearest_strike(ticker, moneyness, trading_day, strike_prices):
    spot_price = get_spot_for_trading_day(ticker, trading_day)
    strike_prices = np.array(strike_prices)/1000
    target_strike = moneyness * spot_price    
    differences = np.abs(np.array(strike_prices) - target_strike)    
    min_diff_idx = np.argmin(differences)
    min_diff = differences[min_diff_idx]
    candidates = [strike for i, strike in enumerate(strike_prices) if differences[i] == min_diff]
    return min(candidates)*1000



@lru_cache(maxsize=128)
def get_paired_expiration_and_strike_for_all_available_expirations_as_polars (ticker):
    return pl.DataFrame(flatten_list(get_paired_expiration_and_strike_for_all_available_expirations(ticker)), schema=['trading_day', 'expiration_day', 'strike', 'ticker'], orient='row')    

@lru_cache(maxsize=128)
def get_unique_trading_days (ticker):
    return get_paired_expiration_and_strike_for_all_available_expirations_as_polars(ticker).filter(pl.col('trading_day').is_in(get_median_price_dataframe().filter(pl.col('ticker') == ticker)['date'])).select(['trading_day', 'expiration_day']).unique().sort('trading_day')

def subset_strikes (ticker, trading, expiration):
    df = get_paired_expiration_and_strike_for_all_available_expirations_as_polars(ticker)
    if not len(df):
        return pl.DataFrame
    trading_expiration_pair = df.filter((pl.col('trading_day') == trading) & (pl.col('expiration_day') == expiration) & (pl.col('ticker') == ticker))
    nearest_strikes = [find_nearest_strike(ticker, moneyness/10, trading, trading_expiration_pair['strike'].to_numpy()) for moneyness in range(3,14,1)]
    if nearest_strikes:
        return trading_expiration_pair.filter(pl.col('strike').is_in(nearest_strikes))
    else:
        append_log(f"No strikes found for {ticker} for trading day {trading} and expiration day {expiration}", level='ERROR', log_file=f'logs/data_fetcher.log')
        return pl.DataFrame(schema=trading_expiration_pair.schema)

def get_relevant_expirations_and_strikes (ticker):
    return pl.concat(subset_strikes(ticker, trading_day, expiration_day) for trading_day, expiration_day in get_unique_trading_days(ticker).iter_rows()).join(get_median_price_dataframe().filter(pl.col('ticker') == ticker).drop('ticker'), left_on='trading_day', right_on='date').sort('trading_day')

@time_it
def parallel_fetch(ticker):
    paired_expirations_and_strike = [row for row in get_relevant_expirations_and_strikes(ticker).select(['trading_day', 'expiration_day', 'strike','ticker']).iter_rows()]
    append_log(f"We will hit API {len(paired_expirations_and_strike)} times for {ticker}", level='INFO', log_file=f'logs/data_fetcher.log')
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(fetch, tqdm(paired_expirations_and_strike)))
    append_log(f":) All expirations and strikes for {ticker} fetched successfully.", level='INFO', log_file=f'logs/data_fetcher.log')
    df = pl.concat(results)
    df.write_parquet(f'DATA/{ticker}.parquet')
    return None


def append_to_file(filename, text):
    with open(filename, "a") as file:  # Open file in append mode
        file.write(text + "\n")  # Append the text followed by a newline

@lru_cache(maxsize=128)
def read_file(filename='completed_tickers.txt'):
    with open (filename, 'r') as f:
        return f.read().splitlines()
    
def main():
    tickers = pl.read_csv('tickersAndIndustries.csv')['ticker'].to_list()
    for ticker in tqdm(tickers):
        print(ticker)
        if ticker in read_file('completed_tickers.txt'):
            append_log(f"{ticker} already fetched", level='INFO', log_file=f'logs/data_fetcher.log')
            continue
        try:
            parallel_fetch(ticker)
            append_to_file("completed_tickers.txt", "new_string")

        except Exception as e:
            append_log(e, level='ERROR', log_file=f'logs/data_fetcher.log')
            append_log(f"Failed to fetch data for {ticker}", level='ERROR', log_file=f'logs/data_fetcher.log')
            continue


if __name__ == "__main__":
    main()