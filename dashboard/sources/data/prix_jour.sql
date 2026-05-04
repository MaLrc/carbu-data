WITH CTE_prix AS (
  SELECT s_id, p_maj_date, p_carburant, p_prix, ROW_NUMBER() OVER (PARTITION BY s_id, p_carburant ORDER BY p_maj_date DESC) AS rn
  FROM read_parquet('s3://prix-carburants/daily_prices/*/*/data.parquet', hive_partitioning = 1)
  WHERE year = CAST(date_part('year', today()) AS INT)
  AND month >= strftime(today() - 3, '%m')
) 
SELECT s_id, p_maj_date, p_carburant, p_prix
FROM CTE_prix
WHERE rn = 1;