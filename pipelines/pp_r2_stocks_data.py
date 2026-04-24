import yfinance as yf
import polars as pl
from datetime import datetime
from helpers import bucket_name, r2_bucket_storage_options
from loguru import logger


def _get_financial_data(tickers:list, period:str) -> pl.DataFrame:
  pl_df = pl.DataFrame()
  
  fin_df = yf.download(tickers=tickers, period=period)
  if fin_df is not None and not fin_df.empty:
    stacked_df = fin_df.stack(level=1).reset_index()
    pl_df = pl.from_pandas(stacked_df)
  
  return pl_df

def stocks_data_pipeline():
  df = _get_financial_data(['BZ=F'], period='5y')
  path = f's3://{bucket_name}/stocks_data/data.parquet'
  logger.info(f'Uploading to: {path}')
  df.write_parquet(
    path,
    storage_options=r2_bucket_storage_options
  )
