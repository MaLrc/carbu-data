import duckdb
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from helpers import access_key, secret_key, bucket_endpoint_url, r2_bucket_storage_options, bucket_name
from loguru import logger
import polars as pl
from datetime import datetime

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

def _extract_station_info(soup):
  nom_tag = soup.find('p', class_='fr-h2')
  nom = nom_tag.get_text(strip=True) if nom_tag else "N/A"
  
  marque = "Indépendant"
  strong_tag = soup.find('strong', string=lambda s: s and 'Marque' in s)
  if strong_tag:
    raw_marque = strong_tag.next_sibling
    if raw_marque:
      marque = raw_marque.strip().replace(':', '').strip()      
  return nom, marque


def update_stations_infos_pipeline():
  df_stations_infos = pl.DataFrame()
  try :
    df_stations_infos = conn.execute("SELECT * FROM read_parquet('s3://prix-carburants/infos_stations/*.parquet');").pl()
  except Exception as e:
    print("Le fichier infos_stations n'éxiste pas sur le bucket")

  if not df_stations_infos.is_empty():
    latest_update = df_stations_infos['Date_Scraping'].max().strftime('%Y-%m-%d') # type: ignore
    logger.info(f'Search stations infos to update from date : {latest_update}')
    res_to_process = conn.execute(f"""
      WITH cte_processed AS (
        SELECT Id_Pdv
        FROM read_parquet('s3://prix-carburants/infos_stations/*.parquet')
      )
      SELECT DISTINCT s_id 
      FROM read_parquet('s3://prix-carburants/daily_prices/*/*/*/*.parquet') s
      LEFT JOIN cte_processed p
        ON p.Id_Pdv = s.s_id
      WHERE s.p_maj_date >= '{latest_update}'
      AND p.Id_Pdv IS NULL;
    """).fetchall()

  else :
    res_to_process = conn.execute("SELECT DISTINCT s_id FROM read_parquet('s3://prix-carburants/daily_prices/*/*/*/*.parquet');").fetchall()

  liste_ids = [row[0] for row in res_to_process]
  if len(liste_ids) > 0:
    logger.info(f'Found {len(liste_ids)} Pdvs to process')
  else :
    logger.info(f'No Pdvs to update')
    return
    
  new_stations_infos = []

  for station_id in tqdm(liste_ids, unit='station', desc='Scrapping infos stations...'):
    print(f"Traitement de la station : {station_id}")
    
    try:
      url = f"https://www.prix-carburants.gouv.fr/station/{station_id}"
      headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      }
      response = requests.get(url, headers=headers, timeout=10)
      
      if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        nom, marque = _extract_station_info(soup)
        new_stations_infos.append({
          'Id_Pdv': station_id,
          'Nom_Station': nom,
          'Marque': marque,
          'Date_Scraping': datetime.now()
        })
      
    except Exception as e:
      tqdm.write(f"❌ Erreur sur {station_id}: {e}")

  df_new_stations_infos = pl.DataFrame(new_stations_infos)
  df_final = pl.concat([df_stations_infos, df_new_stations_infos])

  path = f's3://{bucket_name}/infos_stations/data.parquet'
  logger.info(f'Uploading to: {path}')

  df_final.write_parquet(
    path,
    storage_options=r2_bucket_storage_options
  )
  
if __name__ == '__main__':
  update_stations_infos_pipeline()