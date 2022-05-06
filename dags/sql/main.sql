#standardSQL
CREATE OR REPLACE TABLE
  `{{ params.DWH_TABLE_NAME }}`
(
  day DATE,
  pv INT64
) 
AS
  SELECT
    day,
    pv
  FROM
    `{{ params.DWH_TABLE_NAME }}`
  UNION ALL
  SELECT
    DATE(`{{ params.target_day }}`) day,
    COUNT(time) pv
  FROM
    `{{ params.SOURCE_TABLE_NAME }}`
