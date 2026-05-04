SELECT p_maj_date, p_carburant, AVG(p_prix) as prix
FROM read_parquet('s3://prix-carburants/daily_prices/*/*/data.parquet', hive_partitioning = 1) px
GROUP BY p_maj_date, p_carburant;