SELECT DISTINCT 
  sta.s_id as id,
  sta.s_latitude as lat,
  sta.s_longitude as lng,
  sta.s_cp as cp,
  sta.s_pop as pop,
  sta.s_adresse as adresse,
  sta.s_ville as ville,
  inf.Nom_Station as nom,
  inf.Marque as marque
FROM read_parquet('s3://prix-carburants/daily_prices/*/*/data.parquet', hive_partitioning = 1) sta
LEFT JOIN read_parquet('s3://prix-carburants/infos_stations/data.parquet', hive_partitioning = 1) inf
  ON inf.Id_Pdv = sta.s_id;