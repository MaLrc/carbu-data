import polars as pl
import os
import s3fs
import re
import shutil
from helpers import _download_zip_file, r2_bucket_storage_options, bucket_name, r2_fs
from datetime import datetime, timedelta, date
from xml.etree import ElementTree as ET
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

BASE_URL_ANNEE = "https://donnees.roulez-eco.fr/opendata/annee"
BASE_URL_JOUR  = "https://donnees.roulez-eco.fr/opendata/jour"
BASE_URL_INSTANTANE  = "https://donnees.roulez-eco.fr/opendata/instantane"

def _iter_pdv(xml_file: Path):
  """
  Itère sur les éléments <pdv> d'un fichier XML local via iterparse
  (streaming — pas de chargement complet en mémoire).
  """
  for _, elem in ET.iterparse(xml_file, events=("end",)):
    if elem.tag == "pdv":
      yield elem
      elem.clear()
 
def _parse_pdv(pdv_elem: ET.Element):
  """Génère un dictionnaire pour chaque prix trouvé dans le point de vente."""
  pdv_id = pdv_elem.get("id")
  adresse_elem = pdv_elem.find("adresse")
  ville_elem = pdv_elem.find("ville")
  
  for prix_elem in pdv_elem.findall("prix"):
    nom = prix_elem.get("nom")
    id = prix_elem.get("id")
    valeur = prix_elem.get("valeur")
    maj = prix_elem.get("maj", '')

    if nom and valeur and maj:
      yield {
        "s_id": pdv_id,
        "s_latitude": pdv_elem.get("latitude"),
        "s_longitude": pdv_elem.get("longitude"),
        "s_cp": pdv_elem.get("cp"),
        "s_pop": pdv_elem.get("pop"),
        "s_adresse": adresse_elem.text if adresse_elem is not None else None,
        "s_ville": ville_elem.text if ville_elem is not None else None,
        'p_carburant_id': id,
        "p_carburant": nom,
        "p_prix": valeur,
        "p_maj": datetime.fromisoformat(maj),
        'p_maj_date': datetime.fromisoformat(maj).date(),
        'year': datetime.fromisoformat(maj).date().year,
        'month': datetime.fromisoformat(maj).date().month,
        'day': datetime.fromisoformat(maj).date().day,
      }
      
def _get_latest_date_on_r2():
  base_path = f"{bucket_name}/daily_prices"
  
  try:
    years = r2_fs.ls(base_path)
    year_folders = [y for y in years if 'year=' in y]
    if not year_folders: return None
    latest_year_path = sorted(year_folders)[-1]
    
    months = r2_fs.ls(latest_year_path)
    month_folders = [m for m in months if 'month=' in m]
    if not month_folders: return None
    latest_month_path = sorted(month_folders)[-1]

    days = r2_fs.ls(latest_month_path)
    day_folders = [d for d in days if "day=" in d]
    latest_day_path = sorted(day_folders)[-1]
    
    match = re.search(r"year=(\d+)/month=(\d+)/day=(\d+)", latest_day_path)
    if match:
      y, m, d = match.groups()
      return datetime.strptime(f'{y}-{m}-{d}', "%Y-%m-%d").date()
  except Exception as e:
    logger.error(f'Error or empty bucket : {e}')
    return None
    
def _generate_parquet(df:pl.DataFrame, min_date:date):
  df = df.filter(
    pl.col('p_maj_date') >= min_date
  ).with_columns(
    (pl.col('s_latitude').cast(pl.Float64)) / 100000, 
    (pl.col('s_longitude').cast(pl.Float64)) / 100000,
    pl.col('p_prix').cast(pl.Float64),
    pl.col('s_id').cast(pl.Int64),
    pl.col('p_carburant_id').cast(pl.Int64),
    pl.col('p_maj').cast(pl.Datetime),
    pl.col('p_maj_date').cast(pl.Date),
    pl.col('year').cast(pl.Int64),
    pl.col('month').cast(pl.Int64),
    pl.col('day').cast(pl.Int64),
  )
  
  partitionned_dfs = df.sort(by='p_maj_date').partition_by(["year", "month", "day"], as_dict=True)
  
  for (y, m, d), df_day in partitionned_dfs.items():
    path = f"s3://{bucket_name}/daily_prices/year={y}/month={m:02d}/day={d:02d}/data.parquet"
    
    logger.info(f'Uploading to: {path}')
    
    df_day.write_parquet(
        path,
        storage_options=r2_bucket_storage_options
    )
    
def _clean_local_data():
  folder = './data'
  if os.path.exists(folder):
      shutil.rmtree(folder)  # Supprime le dossier et tout son contenu
  os.makedirs(folder)        # Recrée le dossier vide
  logger.info('Folder ./data cleared !')

def daily_refresh_pipeline():
  latest_date = _get_latest_date_on_r2()
  today = datetime.now().date()
  
  if latest_date is None:
    logger.warning(f'Unable to determine the latest date.')
    return
  
  start_date = latest_date - timedelta(days=1)
  dates_in_delta = [start_date + timedelta(days=i) for i in range((today - start_date).days + 1)]
  
  if dates_in_delta == []:
    logger.info(f'No dates in delta')
    return None
  
  data = []
  for date in dates_in_delta:
    url = BASE_URL_INSTANTANE if date == today else f'{BASE_URL_JOUR}/{date.strftime('%Y%m%d')}'
    f = _download_zip_file(url, './data')
    if f:
      logger.info('Start parsing data')
      for pdv_elem in _iter_pdv(f):
        lines = list(_parse_pdv(pdv_elem))
        data.extend(lines)
      df = pl.DataFrame(data)
      _generate_parquet(df, date)
  
  _clean_local_data()

def create_history_pipeline(from_year:int):
  current_year = datetime.now().date().year
  years_in_delta = [y for y in range(from_year, current_year+1)]
  print(years_in_delta)
  
  data = []
  for year in years_in_delta:
    url = f'{BASE_URL_ANNEE}/{year}'
    start_of_year = datetime(year, 1, 1).date()
    f = _download_zip_file(url, './data')
    if f:
      logger.info('Start parsing data')
      for pdv_elem in _iter_pdv(f):
        lines = list(_parse_pdv(pdv_elem))
        data.extend(lines)
      df = pl.DataFrame(data)
      _generate_parquet(df, start_of_year)
  
  _clean_local_data()