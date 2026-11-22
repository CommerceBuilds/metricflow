test_name: test_fence_keeps_outer_filters_out_of_the_read
test_filename: test_span_rendering.py
docstring:
  The read ends in `OFFSET 0`, and a flag filter stays outside it.

  Both flags are read in one plan, so the read is shared and each branch filters it from outside.
sql_engine: Postgres
---
-- Combine Aggregated Outputs
-- Write to DataTable
WITH am_90006_cte AS (
  -- Aggregate Inputs for Simple Metrics, filters merged
  SELECT
    metric_time__fiscal_month
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
      , metric_time__fiscal_month
    FROM (
      -- Metric Time Dimension 'ds'
      -- Join to Custom Granularity Dataset
      -- Select: [
      --   '__ending_units',
      --   '__beginning_units',
      --   'inventory_span__span_is_last',
      --   'inventory_span__span_is_first',
      --   'metric_time__fiscal_month',
      -- ]
      SELECT
        subq_90035.fiscal_month AS metric_time__fiscal_month
        , inventory_spans_src_90000.span_is_last AS inventory_span__span_is_last
        , inventory_spans_src_90000.span_is_first AS inventory_span__span_is_first
        , inventory_spans_src_90000.on_hand_units AS ending_units
        , inventory_spans_src_90000.on_hand_units AS beginning_units
      FROM (
        WITH span_periods AS (SELECT d.fiscal_month AS p_key, MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days, ROW_NUMBER() OVER (ORDER BY MIN(d.ds)) AS p_no FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE) GROUP BY d.fiscal_month), span_day_periods AS (SELECT d.ds AS p_day, p.p_no FROM span_test.mf_time_spine d JOIN span_periods p ON p.p_key = d.fiscal_month WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE)) SELECT span.*, sd.*, LEAST(COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1), p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM (SELECT * FROM span_test.fct_inventory_spans span WHERE span.valid_from <= CAST(:range_to AS DATE) AND (span.valid_to > CAST(:range_from AS DATE) OR span.valid_to IS NULL) AND span.valid_from < COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1)) span JOIN span_day_periods lo ON lo.p_day = GREATEST(span.valid_from, CAST(:range_from AS DATE)) JOIN span_day_periods hi ON hi.p_day = LEAST(COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) - 1, CAST(:range_to AS DATE)) CROSS JOIN LATERAL generate_series(lo.p_no, hi.p_no) AS g(p_no) JOIN span_periods p ON p.p_no = g.p_no JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first OFFSET 0
      ) inventory_spans_src_90000
      LEFT OUTER JOIN
        span_test.mf_time_spine subq_90035
      ON
        DATE_TRUNC('day', inventory_spans_src_90000.ds) = subq_90035.ds
    ) subq_90037
    WHERE ((inventory_span__span_is_last = 1)) OR ((inventory_span__span_is_first = 1))
  ) subq_90038
  GROUP BY
    metric_time__fiscal_month
)

SELECT
  COALESCE(subq_90041.metric_time__fiscal_month, subq_90044.metric_time__fiscal_month) AS metric_time__fiscal_month
  , COALESCE(MAX(subq_90041.ending_units), 0) AS ending_units
  , COALESCE(MAX(subq_90044.beginning_units), 0) AS beginning_units
FROM (
  -- Compute Metrics via Expressions
  SELECT
    metric_time__fiscal_month
    , COALESCE(__ending_units, 0) AS ending_units
  FROM (
    -- Aggregate Inputs for Simple Metrics
    SELECT
      __ending_units__fm0_0 AS __ending_units
      , metric_time__fiscal_month
    FROM (
      -- Read From CTE For node_id=am_90006
      SELECT
        metric_time__fiscal_month
        , __ending_units__fm0_0
        , __fm0_0_has
      FROM am_90006_cte
    ) subq_90039
    WHERE __fm0_0_has > 0
  ) subq_90040
) subq_90041
FULL OUTER JOIN (
  -- Compute Metrics via Expressions
  SELECT
    metric_time__fiscal_month
    , COALESCE(__beginning_units, 0) AS beginning_units
  FROM (
    -- Aggregate Inputs for Simple Metrics
    SELECT
      __beginning_units__fm0_1 AS __beginning_units
      , metric_time__fiscal_month
    FROM (
      -- Read From CTE For node_id=am_90006
      SELECT
        metric_time__fiscal_month
        , __beginning_units__fm0_1
        , __fm0_1_has
      FROM am_90006_cte
    ) subq_90042
    WHERE __fm0_1_has > 0
  ) subq_90043
) subq_90044
ON
  subq_90041.metric_time__fiscal_month = subq_90044.metric_time__fiscal_month
GROUP BY
  COALESCE(subq_90041.metric_time__fiscal_month, subq_90044.metric_time__fiscal_month)
