import logging
import polars as pl
from functools import lru_cache

def append_log(message, level='ERROR', log_file='app.log'):
    # Set up basic logging configuration
    logging.basicConfig(filename=log_file,
                        filemode='a',  # Append mode
                        format='[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)  # Setting to DEBUG ensures all levels are logged

    # Create a logger object
    logger = logging.getLogger()

    # Map log level to the corresponding logging function
    log_levels = {
        'DEBUG': logger.debug,
        'INFO': logger.info,
        'WARNING': logger.warning,
        'ERROR': logger.error,
        'CRITICAL': logger.critical
    }

    # Log the message with the specified or default log level
    log_func = log_levels.get(level.upper(), logger.error)  # Default to ERROR if level is invalid
    log_func(message)


@lru_cache(maxsize=32)
def read_data (ticker):
    return pl.read_parquet(f'data/{ticker}.parquet')
def filter_moneyness (level, epsilon=0.05):
    return pl.col('moneyness').is_between(level-epsilon, level+epsilon)

def get_sanitized_options_data (ticker):
    data = read_data(ticker)
    sanitize_strike = [pl.col('strike')/1000]
    sanitize_dates = [pl.col(col).str.to_date('%Y%m%d') for col in ['date', 'expiration']]
    moneyness = [(pl.col('strike')/pl.col('underlying_price')).alias('moneyness')]
    return data.with_columns(sanitize_strike+sanitize_dates).with_columns(moneyness).with_columns(
    (pl.col("date").cast(pl.Datetime("ms")) +pl.duration(milliseconds=pl.col("ms_of_day"))).alias("timestamp")
)

@lru_cache(maxsize=32)
def get_quote_data (ticker, path='data/quote_data.parquet'):
    quotes = pl.scan_parquet(path).filter(pl.col('ticker') == ticker).collect()
    mid_volume = (pl.col("ask_size") / (pl.col("ask_size") + pl.col("bid_size")))
    mid_price = pl.col("ask") * (mid_volume) + pl.col("bid") * (1-mid_volume)
    quotes = quotes.with_columns(mid_price.alias("weighted_mid_price"))
    quotes = quotes.with_columns((pl.col("ask") - pl.col("bid")).alias("spread"))
    quotes = quotes.with_columns(
        (
            ((pl.col("ask_size") * pl.col("spread")) + (pl.col("bid_size") * pl.col("spread"))) / 
            (pl.col("bid_size") + pl.col("ask_size"))
        ).alias("volume_weighted_spread")
    ).with_columns(
    (pl.col("date").cast(pl.Datetime("ms")) +pl.duration(milliseconds=pl.col("ms_of_day"))).alias("timestamp")
)
    return quotes


import numpy as np

def truncate_array(arr, lower_quantile=0.01, upper_quantile=0.99): 
    # Calculate the lower and upper quantile values
    lower_bound = np.quantile(arr, lower_quantile)
    upper_bound = np.quantile(arr, upper_quantile)
    
    # Truncate the array
    truncated_arr = arr[(arr >= lower_bound) & (arr <= upper_bound)]
    
    return truncated_arr

def scale_array(arr, method='standard'):
    arr = np.array(arr)  # Ensure input is a NumPy array
    
    if method == 'standard':
        mean = np.mean(arr)
        std = np.std(arr)
        scaled_arr = (arr - mean) / std
    elif method == 'minmax':
        min_val = np.min(arr)
        max_val = np.max(arr)
        scaled_arr = (arr - min_val) / (max_val - min_val)
    else:
        raise ValueError("Method must be either 'standard' or 'minmax'.")
    
    return scaled_arr


import numpy as np

def ema_smoothing(arr, alpha):
    """
    Applies an Exponential Moving Average (EMA) smoothing filter to a Numpy array.
    
    Parameters:
    - arr: Numpy array of data to be smoothed
    - alpha: Smoothing factor, a float between 0 and 1. Higher values of alpha give more weight to recent data.
    
    Returns:
    - smoothed_arr: Numpy array with the same length as the input array, but smoothed using EMA
    """
    if not 0 < alpha <= 1:
        raise ValueError("Alpha should be a value between 0 and 1.")
    
    # Initialize the smoothed array with the same shape as input
    smoothed_arr = np.zeros_like(arr, dtype=np.float64)
    
    # Set the first element as the first smoothed value
    smoothed_arr[0] = arr[0]
    
    # Apply EMA smoothing to the rest of the array
    for t in range(1, len(arr)):
        smoothed_arr[t] = alpha * arr[t] + (1 - alpha) * smoothed_arr[t - 1]
    
    return smoothed_arr
