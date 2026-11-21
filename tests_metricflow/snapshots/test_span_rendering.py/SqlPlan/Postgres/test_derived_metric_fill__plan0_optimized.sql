test_name: test_derived_metric_fill
test_filename: test_span_rendering.py
docstring:
  A derived metric with `config.meta.fill_nulls_with` fills in the select that combines metrics' outputs.
sql_engine: Postgres
---
-- Combine Aggregated Outputs
-- Write to DataTable
WITH rss_90001_cte AS NOT MATERIALIZED (
  -- Read Elements From Semantic Model 'inventory_spans'
  SELECT
    on_hand_units AS __ending_units
    , on_hand_units AS __beginning_units
    , DATE_TRUNC('week', ds) AS ds__week
    , span_is_last AS inventory_span__span_is_last
    , span_is_first AS inventory_span__span_is_first
  FROM (
    WITH span_periods AS (SELECT CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE) AS p_key, MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE) GROUP BY CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE)) SELECT span.*, sd.*, LEAST(span.valid_to, p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND span.valid_to > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND span.valid_to > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM (SELECT * FROM span_test.fct_inventory_spans span WHERE span.valid_from <= CAST(:range_to AS DATE) AND span.valid_to > CAST(:range_from AS DATE) AND span.valid_from < span.valid_to) span CROSS JOIN LATERAL generate_series(DATE_TRUNC('week', CAST(GREATEST(span.valid_from, CAST(:range_from AS DATE)) AS TIMESTAMP)), DATE_TRUNC('week', CAST(LEAST(span.valid_to - 1, CAST(:range_to AS DATE)) AS TIMESTAMP)), INTERVAL '1 week') AS g(p_start) JOIN span_periods p ON p.p_key = CAST(g.p_start AS DATE) JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first OFFSET 0
  ) inventory_spans_src_90000
)

, cm_90010_cte AS (
  -- Constrain Output with WHERE
  -- Select: ['__ending_units', 'metric_time__week']
  -- Aggregate Inputs for Simple Metrics
  -- Compute Metrics via Expressions
  SELECT
    metric_time__week
    , SUM(ending_units) AS ending_units
  FROM (
    -- Read From CTE For node_id=rss_90001
    -- Metric Time Dimension 'ds'
    -- Select: ['__ending_units', 'inventory_span__span_is_last', 'metric_time__week']
    SELECT
      ds__week AS metric_time__week
      , inventory_span__span_is_last
      , __ending_units AS ending_units
    FROM rss_90001_cte
  ) subq_90029
  WHERE inventory_span__span_is_last = 1
  GROUP BY
    metric_time__week
)

, cm_90011_cte AS (
  -- Constrain Output with WHERE
  -- Select: ['__beginning_units', 'metric_time__week']
  -- Aggregate Inputs for Simple Metrics
  -- Compute Metrics via Expressions
  SELECT
    metric_time__week
    , SUM(beginning_units) AS beginning_units
  FROM (
    -- Read From CTE For node_id=rss_90001
    -- Metric Time Dimension 'ds'
    -- Select: ['__beginning_units', 'inventory_span__span_is_first', 'metric_time__week']
    SELECT
      ds__week AS metric_time__week
      , inventory_span__span_is_first
      , __beginning_units AS beginning_units
    FROM rss_90001_cte
  ) subq_90036
  WHERE inventory_span__span_is_first = 1
  GROUP BY
    metric_time__week
)

SELECT
  COALESCE(subq_90042.metric_time__week, subq_90046.metric_time__week, subq_90052.metric_time__week) AS metric_time__week
  , COALESCE(MAX(subq_90042.unit_change), 0) AS unit_change
  , MAX(subq_90046.unit_change_unfilled) AS unit_change_unfilled
  , MAX(subq_90052.received_units) AS received_units
FROM (
  -- Compute Metrics via Expressions
  SELECT
    metric_time__week
    , ending_units - beginning_units AS unit_change
  FROM (
    -- Combine Aggregated Outputs
    SELECT
      COALESCE(cm_90010_cte.metric_time__week, cm_90011_cte.metric_time__week) AS metric_time__week
      , MAX(cm_90010_cte.ending_units) AS ending_units
      , MAX(cm_90011_cte.beginning_units) AS beginning_units
    FROM cm_90010_cte
    FULL OUTER JOIN
      cm_90011_cte
    ON
      cm_90010_cte.metric_time__week = cm_90011_cte.metric_time__week
    GROUP BY
      COALESCE(cm_90010_cte.metric_time__week, cm_90011_cte.metric_time__week)
  ) subq_90041
) subq_90042
FULL OUTER JOIN (
  -- Compute Metrics via Expressions
  SELECT
    metric_time__week
    , ending_units - beginning_units AS unit_change_unfilled
  FROM (
    -- Combine Aggregated Outputs
    SELECT
      COALESCE(cm_90010_cte.metric_time__week, cm_90011_cte.metric_time__week) AS metric_time__week
      , MAX(cm_90010_cte.ending_units) AS ending_units
      , MAX(cm_90011_cte.beginning_units) AS beginning_units
    FROM cm_90010_cte
    FULL OUTER JOIN
      cm_90011_cte
    ON
      cm_90010_cte.metric_time__week = cm_90011_cte.metric_time__week
    GROUP BY
      COALESCE(cm_90010_cte.metric_time__week, cm_90011_cte.metric_time__week)
  ) subq_90045
) subq_90046
ON
  subq_90042.metric_time__week = subq_90046.metric_time__week
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
) subq_90052
ON
  COALESCE(subq_90042.metric_time__week, subq_90046.metric_time__week) = subq_90052.metric_time__week
GROUP BY
  COALESCE(subq_90042.metric_time__week, subq_90046.metric_time__week, subq_90052.metric_time__week)
