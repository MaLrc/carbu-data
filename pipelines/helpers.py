import io
import dotenv
import os
import zipfile
import requests
import s3fs
from loguru import logger
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def _download_zip_file(url: str, dest: str) -> Path | None:
  try:
    logger.info(f'Downloading from {url}')
    resp = requests.get(url)
    resp.raise_for_status()
  except requests.RequestException as e:
    logger.error("Impossible de télécharger %s : %s", url, e)
    return None

  try : 
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    filename = zf.namelist()[0]
    zf.extract(member=filename, path=dest)
    logger.info(f'Extracting file : {filename}')
    return Path(dest, filename)
  except Exception as e:
    logger.error(f'Error during file extraction : {e}')
    

access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
account_id = os.getenv("R2_ACCOUNT_ID")
bucket_name = os.getenv("R2_BUCKET_NAME")
bucket_endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

r2_bucket_storage_options = {
  "aws_access_key_id": access_key,
  "aws_secret_access_key": secret_key,
  "aws_endpoint": bucket_endpoint_url,
  "aws_region": "auto",
  "aws_s3_addressing_style": "path"
}

r2_fs = s3fs.S3FileSystem(
  key=access_key,
  secret=secret_key,
  endpoint_url=bucket_endpoint_url
)