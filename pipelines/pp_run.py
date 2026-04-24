from pp_r2_daily_prices import daily_refresh_pipeline, create_history_pipeline
from pp_r2_stocks_data import stocks_data_pipeline
from pp_r2_communes import communes_data_pipeline
from pp_r2_infos_stations import update_stations_infos_pipeline
from loguru import logger
import click

@click.command()
@click.option('--from-year', 'from_year', default=None, )
def run_pipelines(from_year):
  if from_year:
    logger.info(f'RUN create_history_pipeline - From Year {from_year}')
    create_history_pipeline(from_year)
  else :
    logger.info('RUN daily_refresh_pipeline')
    daily_refresh_pipeline()
    
  logger.info('RUN stocks_data_pipeline')
  stocks_data_pipeline()
    
  logger.info('RUN communes_data_pipeline')
  communes_data_pipeline()
  
  logger.info('RUN update_stations_infos_pipeline')
  update_stations_infos_pipeline()
    
if __name__ == '__main__':
  run_pipelines()