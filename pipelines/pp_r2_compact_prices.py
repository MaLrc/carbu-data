import duckdb
from helpers import access_key, secret_key, bucket_endpoint_url, r2_fs, bucket_name
from loguru import logger
import re

def _compact_month(year, month):
  conn = duckdb.connect()
  conn.execute("INSTALL httpfs; LOAD httpfs;")

  conn.execute(f"""
      CREATE SECRET r2_config (
          TYPE S3,
          KEY_ID '{access_key}',
          SECRET '{secret_key}',
          ENDPOINT '{bucket_endpoint_url.replace('https://', '')}',
          URL_STYLE 'path',
          REGION 'auto'
      );
  """)

  source_path = f"s3://prix-carburants/daily_prices/year={year}/month={month}/*/*.parquet"
  target_path = f"s3://prix-carburants/daily_prices/year={year}/month={month}/data.parquet"
  
  logger.info(f'Compaction de {year}-{month}...')
  
  conn.execute(f"""
    COPY (SELECT * FROM read_parquet('{source_path}'))
    TO '{target_path}' (FORMAT 'PARQUET', COMPRESSION 'ZSTD');
  """)
  
  logger.info(f'Compaction terminée : {target_path}')

def compact_daily_files_pipeline():
  base_path = f"{bucket_name}/daily_prices"
  list_months = []
  
  try:
    years = r2_fs.ls(base_path)
    year_folders = [y for y in years if 'year=' in y]
    if not year_folders: return None
    for y in year_folders:
      months = r2_fs.ls(y)
      month_folders = [m for m in months if 'month=' in m]
      if not month_folders: return None
      for m in month_folders:
        list_months.append(m)
    
    print(list_months, list_months.sort(reverse=True))
    for idx, m_path in enumerate(list_months):
      if not r2_fs.isfile(f'{m_path}/data.parquet') or idx <= 1 :
        match = re.search(r"year=(\d+)/month=(\d+)", m_path)
        if match:
          y, m = match.groups()
          _compact_month(y, m)
          
  except Exception as e:
    logger.error(f'Error : {e}')

  
if __name__ == '__main__':
  compact_daily_files_pipeline()