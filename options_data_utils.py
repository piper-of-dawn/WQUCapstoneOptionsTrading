from functools import lru_cache
import datetime
import numpy as np
from visualisation import plotly_utils as pu
import plotly.express as px
import polars as pl
import plotly
import plotly.io as pioget



def reorder(self, new_position, col_name):
    neworder=self.columns
    neworder.remove(col_name)
    neworder.insert(new_position,col_name)
    return self.select(neworder)
pl.DataFrame.reorder=reorder
del reorder

def cast_to_date(self, col_name, format='%Y%m%d'):
    return self.with_columns([pl.col(col_name).str.to_date(format).alias(col_name)])
pl.DataFrame.cast_to_date=cast_to_date
del cast_to_date

def filter_strike (self, strike):
    return self.filter(pl.col('strike') == strike)

def filter_day(self, day):
    if isinstance(day, str):
        day = datetime.datetime.strptime(day, '%Y%m%d')
    return self.filter(pl.col('trading_day') == day)

def filter_expiration(self, day):
    if isinstance(day, str):
        day = datetime.datetime.strptime(day, '%Y%m%d')
    return self.filter(pl.col('expiration') == day)

def filter_delta (self, delta, epsilon=0.01):    
    return self.filter(pl.col('delta').is_between(delta-epsilon, delta+epsilon))

def filter_days_to_expiry (self, between):
    lower, upper = between
    return self.filter(pl.col('days_to_expiry').abs().is_between(lower, upper))

pl.DataFrame.filter_days_to_expiry = filter_days_to_expiry 
pl.DataFrame.filter_strike=filter_strike
pl.DataFrame.filter_day=filter_day
pl.DataFrame.filter_expiration=filter_expiration
pl.DataFrame.filter_delta=filter_delta

def filter_atm (self):
    return self.with_columns([(pl.col("strike") - pl.col("underlying_price")*1000).abs().alias('strike_distance'),
                          (pl.col('trading_day')-pl.col('expiration')).dt.total_days().alias('days_to_expiry')]).filter(pl.col('strike_distance') == pl.col('strike_distance').min())
    
def filter_otm_based_on_delta (self):
    return self.with_columns(pl.col('delta').abs().is_between(0.2, 0.3))


def filter_atm_based_on_delta (self):
    return self.filter(pl.col('delta').abs().is_between(0.45, 0.55))

pl.DataFrame.filter_otm_based_on_delta = filter_otm_based_on_delta
pl.DataFrame.filter_atm_based_on_delta = filter_atm_based_on_delta
@lru_cache(maxsize=32)
def read_raw_data(ticker, between, option_type):
    folderpath = f"C:/git/MSThesis/{option_type}/{ticker}/"   
    filepath = f"{folderpath}{ticker}_{between[0]}_{between[1]}.parquet"
    try:
        return pl.read_parquet(filepath)
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return None
    
def concat_data(ticker, option_type):
    return pl.concat(read_raw_data(ticker, between, option_type) for between in [(2019, 2020),(2021, 2022), (2023, 2024)]  )

# .filter(pl.col('date') == '20190930')

def get_cleaned_options_data (ticker, type='CALL'):
    filter_out_zero_implied_vol = pl.col('implied_vol') > 0
    df = concat_data(ticker, type).filter(filter_out_zero_implied_vol)
    zero_price = ((pl.col('bid') == 0) & (pl.col('ask') == 0))
    df = df.filter(zero_price.not_()).with_columns(
        ((pl.col('bid')+pl.col('ask'))/2.0).alias('price'),
        
        (pl.col("date").cast(pl.Utf8)  # Convert date to string
        .str.strptime(pl.Datetime, "%Y%m%d")  # Parse the date from YYYYMMDD
        + pl.duration(milliseconds=pl.col("ms_of_day"))  # Add the milliseconds
        ).alias("timestamp")
).with_columns([
    pl.col('timestamp').dt.date().alias('trading_day'),
    -(pl.col('bid')-pl.col('ask')).alias('spread'),    
    ]).drop(["date", "ms_of_day", "ms_of_day2", 'bid', 'ask']).cast_to_date("expiration").reorder(0,'ticker').reorder(1,'timestamp').reorder(2,'expiration').reorder(2,'strike').sort("timestamp")

    df = df.with_columns([(pl.col("strike") - pl.col("underlying_price")*1000).abs().alias('strike_distance'),
                          (pl.col('expiration')-pl.col('trading_day')).dt.total_days().alias('days_to_expiry')])
    return df


delta_thresholds_puts = {
    "very_deep_otm_put": (-0.10, 0.0),
    "deep_otm_put": (-0.20, -0.10),
    "otm_put": (-0.45, -0.35),
    "around_atm_put": (-0.55, -0.45),
    "itm_put": (-0.75, -0.65),
    "deep_itm_put": (-0.90, -0.80),
    "very_deep_itm_put": (-1.0, -0.90)
}


delta_thresholds_calls = {
    "very_deep_otm_call": (0.0, 0.10),
    "deep_otm_call": (0.10, 0.20),
    "otm_call": (0.35, 0.45),
    "around_atm_call": (0.45, 0.55),
    "itm_call": (0.65, 0.75),
    "deep_itm_call": (0.80, 0.90),
    "very_deep_itm_call": (0.90, 1.0)
}


def get_vol_of_iv_for_delta_bucket(options_data: pl.DataFrame, delta_thresholds: dict, bucket: str):
  return options_data.group_by("trading_day").agg([
      pl.col("implied_vol")
        .filter(pl.col("delta").is_between(*delta_thresholds[bucket]))
        .std()
        .alias(bucket + "_iv")
  ]).sort("trading_day")



def get_average_iv_for_delta_bucket(options_data: pl.DataFrame, delta_thresholds: dict, bucket: str):
  return options_data.group_by("trading_day").agg([
      pl.col("implied_vol")
        .filter(pl.col("delta").is_between(*delta_thresholds[bucket]))
        .mean()
        .alias(bucket + "_iv")
  ]).sort("trading_day")
  
  
def get_number_of_quotes (options_data: pl.DataFrame, delta_thresholds: dict, bucket: str):
    return options_data.group_by("trading_day").agg([
        pl.col("implied_vol")
            .filter(pl.col("delta").is_between(*delta_thresholds[bucket]))
            .count()
            .alias(bucket + "_count")
    ]).sort("trading_day")
    
    
covid=pl.col('trading_day')>datetime.date(2021,5,1)
delta_is_zero_or_one = (pl.col('delta').is_in([0, 1]))

def filter_out_crazy_vrps (self):
    return self.filter(self['vrp'].is_between(self['vrp'].quantile(0.0), self['vrp'].quantile(0.999)))

def housekeeping (ticker):
    df = pl.read_parquet(f"DATA/CLEANED_OPTIONS_DATA/CALL/{ticker}.parquet")
    df = df.filter(pl.col('underlying_price')!=0).filter(delta_is_zero_or_one.not_())
    df = df.with_columns(
        (pl.col('implied_vol') / pl.col('realized_volatility')).alias('vrp')
    ).filter_out_crazy_vrps()
    return df

import datetime



def get_atm_vrps (ticker):
    df = housekeeping(ticker).filter_atm_based_on_delta()
    return df

def get_otm_vrps (ticker):
    df = housekeeping(ticker).filter_otm_based_on_delta()
    return df


pl.DataFrame.filter_out_crazy_vrps = filter_out_crazy_vrps