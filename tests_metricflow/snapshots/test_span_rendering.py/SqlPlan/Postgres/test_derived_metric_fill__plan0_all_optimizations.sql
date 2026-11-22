test_name: test_derived_metric_fill
test_filename: test_span_rendering.py
docstring:
  A derived metric with `config.meta.fill_nulls_with` fills in the select that combines metrics' outputs.
sql_engine: Postgres
---
-- Combine Aggregated Outputs
-- Write to DataTable
WITH am_90009_cte AS (
  -- Aggregate Inputs for Simple Metrics, filters merged
  SELECT
    metric_time__week
    , SUM(CASE WHEN (inventory_span__span_is_last = 1) THEN __ending_units END) AS __ending_units__fm0_0
    , SUM(CASE WHEN (inventory_span__span_is_last = 1) THEN 1 END) AS __fm0_0_has
    , SUM(CASE WHEN (inventory_span__span_is_first = 1) THEN __beginning_units END) AS __beginning_units__fm0_1
    , SUM(CASE WHEN (inventory_span__span_is_first = 1) THEN 1 END) AS __fm0_1_has
  FROM (
    -- Constrain Output with WHERE
    SELECT
      ending_units AS __ending_units
      , beginning_units AS __beginning_units
      , inventory_span__span_is_last
      , inventory_span__span_is_first
      , metric_time__week
    FROM (
      -- Read Elements From Semantic Model 'inventory_spans'
      -- Metric Time Dimension 'ds'
      -- Select: [
      --   '__ending_units',
      --   '__beginning_units',
      --   'inventory_span__span_is_last',
      --   'inventory_span__span_is_first',
      --   'metric_time__week',
      -- ]
      SELECT
        DATE_TRUNC('week', ds) AS metric_time__week
        , span_is_last AS inventory_span__span_is_last
        , span_is_first AS inventory_span__span_is_first
        , on_hand_units AS ending_units
        , on_hand_units AS beginning_units
      FROM (
        WITH span_periods AS (SELECT CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE) AS p_key, MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE) GROUP BY CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE)) SELECT span.*, sd.*, LEAST(COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1), p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM (SELECT * FROM span_test.fct_inventory_spans span WHERE span.valid_from <= CAST(:range_to AS DATE) AND (span.valid_to > CAST(:range_from AS DATE) OR span.valid_to IS NULL) AND span.valid_from < COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1)) span CROSS JOIN LATERAL generate_series(DATE_TRUNC('week', CAST(GREATEST(span.valid_from, CAST(:range_from AS DATE)) AS TIMESTAMP)), DATE_TRUNC('week', CAST(LEAST(COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) - 1, CAST(:range_to AS DATE)) AS TIMESTAMP)), INTERVAL '1 week') AS g(p_start) JOIN span_periods p ON p.p_key = CAST(g.p_start AS DATE) JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first OFFSET 0
      ) inventory_spans_src_90000
    ) subq_90056
    WHERE ((inventory_span__span_is_last = 1)) OR ((inventory_span__span_is_first = 1))
  ) subq_90057
  GROUP BY
    metric_time__week
)

, cm_90025_cte AS NOT MATERIALIZED (
  -- Compute Metrics via Expressions
  SELECT
    metric_time__week
    , COALESCE(__ending_units, 0) AS ending_units
  FROM (
    -- Aggregate Inputs for Simple Metrics
    SELECT
      __ending_units__fm0_0 AS __ending_units
      , metric_time__week
    FROM (
      -- Read From CTE For node_id=am_90009
      SELECT
        metric_time__week
        , __ending_units__fm0_0
        , __fm0_0_has
      FROM am_90009_cte
    ) subq_90058
    WHERE __fm0_0_has > 0
  ) subq_90059
)

, cm_90026_cte AS NOT MATERIALIZED (
  -- Compute Metrics via Expressions
  SELECT
    metric_time__week
    , COALESCE(__beginning_units, 0) AS beginning_units
  FROM (
    -- Aggregate Inputs for Simple Metrics
    SELECT
      __beginning_units__fm0_1 AS __beginning_units
      , metric_time__week
    FROM (
      -- Read From CTE For node_id=am_90009
      SELECT
        metric_time__week
        , __beginning_units__fm0_1
        , __fm0_1_has
      FROM am_90009_cte
    ) subq_90061
    WHERE __fm0_1_has > 0
  ) subq_90062
)

SELECT
  COALESCE(subq_90070.metric_time__week, subq_90076.metric_time__week) AS metric_time__week
  , COALESCE(MAX(subq_90070.unit_change), 0) AS unit_change
  , MAX(subq_90070.unit_change_unfilled) AS unit_change_unfilled
  , MAX(subq_90076.received_units) AS received_units
FROM (
  -- Combine Aggregated Outputs
  SELECT
    COALESCE(subq_90065.metric_time__week, subq_90069.metric_time__week) AS metric_time__week
    , COALESCE(MAX(subq_90065.unit_change), 0) AS unit_change
    , MAX(subq_90069.unit_change_unfilled) AS unit_change_unfilled
  FROM (
    -- Compute Metrics via Expressions
    SELECT
      metric_time__week
      , ending_units - beginning_units AS unit_change
    FROM (
      -- Combine Aggregated Outputs
      SELECT
        COALESCE(subq_90060.metric_time__week, subq_90063.metric_time__week) AS metric_time__week
        , COALESCE(MAX(subq_90060.ending_units), 0) AS ending_units
        , COALESCE(MAX(subq_90063.beginning_units), 0) AS beginning_units
      FROM (
        -- Read From CTE For node_id=cm_90025
        SELECT
          metric_time__week
          , ending_units
        FROM cm_90025_cte
      ) subq_90060
      FULL OUTER JOIN (
        -- Read From CTE For node_id=cm_90026
        SELECT
          metric_time__week
          , beginning_units
        FROM cm_90026_cte
      ) subq_90063
      ON
        subq_90060.metric_time__week = subq_90063.metric_time__week
      GROUP BY
        COALESCE(subq_90060.metric_time__week, subq_90063.metric_time__week)
    ) subq_90064
  ) subq_90065
  FULL OUTER JOIN (
    -- Compute Metrics via Expressions
    SELECT
      metric_time__week
      , ending_units - beginning_units AS unit_change_unfilled
    FROM (
      -- Combine Aggregated Outputs
      SELECT
        COALESCE(subq_90066.metric_time__week, subq_90067.metric_time__week) AS metric_time__week
        , COALESCE(MAX(subq_90066.ending_units), 0) AS ending_units
        , COALESCE(MAX(subq_90067.beginning_units), 0) AS beginning_units
      FROM (
        -- Read From CTE For node_id=cm_90025
        SELECT
          metric_time__week
          , ending_units
        FROM cm_90025_cte
      ) subq_90066
      FULL OUTER JOIN (
        -- Read From CTE For node_id=cm_90026
        SELECT
          metric_time__week
          , beginning_units
        FROM cm_90026_cte
      ) subq_90067
      ON
        subq_90066.metric_time__week = subq_90067.metric_time__week
      GROUP BY
        COALESCE(subq_90066.metric_time__week, subq_90067.metric_time__week)
    ) subq_90068
  ) subq_90069
  ON
    subq_90065.metric_time__week = subq_90069.metric_time__week
  GROUP BY
    COALESCE(subq_90065.metric_time__week, subq_90069.metric_time__week)
) subq_90070
FULL OUTER JOIN (
  -- Read Elements From Semantic Model 'receipts'
  -- Metric Time Dimension 'ds'
  -- Select: ['__received_units', 'metric_time__week']
  -- Select: ['__received_units', 'metric_time__week']
  -- Aggregate Inputs for Simple Metrics
  -- Compute Metrics via Expressions
  SELECT
    DATE_TRUNC('week', ds) AS metric_time__week
    , SUM(received_units) AS received_units
  FROM span_test.fct_receipts receipts_src_90000
  GROUP BY
    DATE_TRUNC('week', ds)
) subq_90076
ON
  subq_90070.metric_time__week = subq_90076.metric_time__week
GROUP BY
  COALESCE(subq_90070.metric_time__week, subq_90076.metric_time__week)
