SELECT s_id, p_maj_date, p_carburant, p_prix
FROM read_parquet('s3://prix-carburants/daily_prices/*/*/*/*.parquet', hive_partitioning = 1)
WHERE year = CAST(date_part('year', today()) AS INT)
AND month = CAST(date_part('month', today()) AS INT)
AND day = CAST(date_part('day', today()) AS INT);