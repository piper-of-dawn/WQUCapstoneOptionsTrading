import polars as pl
import numpy as np
from functools import lru_cache
from toolbox import  get_quote_data

def get_ohlc_data(ticker, every="5m"):
    get_rid_of_nans = pl.all_horizontal(pl.col(pl.Float32, pl.Float64).is_not_nan())
    df = get_quote_data(ticker, path="DATA/quote_data.parquet").filter(
        get_rid_of_nans
    )  # Some 5 minute intervals contain NaNs
    ohlc_data = df.group_by_dynamic("timestamp", every=every).agg(
        pl.col("weighted_mid_price").first().alias("open"),
        pl.col("weighted_mid_price").max().alias("high"),
        pl.col("weighted_mid_price").min().alias("low"),
        pl.col("weighted_mid_price").last().alias("close"),
        np.log(
            pl.col("weighted_mid_price").last() / pl.col("weighted_mid_price").first()
        ).alias(f"log_return_{every}"),
        pl.col("spread").mean().alias("mean_spread"),
    )
    ohlc_data = ohlc_data.drop_nulls()
    return ohlc_data


def get_daily_volatility(ticker):
    scale = np.sqrt(6.5 * 60 / 5)
    ohlc = get_ohlc_data(ticker)
    filter_out_crazy_returns = pl.col("log_return_5m").is_between(
        ohlc["log_return_5m"].quantile(0.01), ohlc["log_return_5m"].quantile(0.99)
    )
    ohlc = ohlc.filter(filter_out_crazy_returns)
    daily_volatility = ohlc.group_by(pl.col("timestamp").dt.date()).agg(
        [
            (pl.col("log_return_5m").sum().exp() - 1).alias("daily_return"),
            ((pl.col("log_return_5m").std()) * scale).alias("daily_volatility"),
            pl.col("mean_spread").mean(),
        ]
    )
    return daily_volatility

@lru_cache(maxsize=128)
def get_volatility_array (ticker):   
    array = get_daily_volatility(ticker)['daily_volatility'].to_numpy()
    assert not np.isnan(array).any(), f"There are {np.sum(np.isnan(array))} NaNs in the array for {ticker}"
    assert not np.isinf(array).any(),f"There are Infinities in the array for {ticker}"
    return array