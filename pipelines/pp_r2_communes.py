import polars as pl 
import requests
import io
from helpers import bucket_name, r2_bucket_storage_options, r2_fs
from loguru import logger


URL = 'https://www.data.gouv.fr/api/1/datasets/r/f5df602b-3800-44d7-b2df-fa40a0350325'

FILE_SCHEMA = {
  'population': pl.Float64,
  'superficie_hectare': pl.Float64,
  'superficie_km2': pl.Float64,
  'densite': pl.Float64,
  'altitude_moyenne': pl.Float64,
  'altitude_minimale': pl.Float64,
  'altitude_maximale': pl.Float64,
  'latitude_mairie': pl.Float64,
  'longitude_mairie': pl.Float64,
  'latitude_centre': pl.Float64,
  'longitude_centre': pl.Float64,
}

def communes_data_pipeline():
  path = f's3://{bucket_name}/communes_data/data.parquet'
  
  if not r2_fs.exists(path):
    df = pl.read_csv(
      URL, 
      infer_schema_length=0, 
      schema_overrides=FILE_SCHEMA
    )
    
    
    logger.info(f'Uploading to: {path}')
    
    df.write_parquet(
      path,
      storage_options=r2_bucket_storage_options
    )
