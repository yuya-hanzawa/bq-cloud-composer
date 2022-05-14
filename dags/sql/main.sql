#standardSQL
CREATE OR REPLACE TABLE
  `{{ params.DWH_TABLE_NAME }}`
(
  executed_date DATE,
  pv INTEGER	
)
PARTITION BY day
AS
  SELECT
    executed_date,
    pv
  FROM
    `{{ params.DWH_TABLE_NAME }}`
  UNION ALL
  SELECT
    DATE('{{ params.TARGET_DAY }}') executed_date,
    COUNT(time) pv
  FROM
    `{{ params.SOURCE_TABLE_NAME }}`
