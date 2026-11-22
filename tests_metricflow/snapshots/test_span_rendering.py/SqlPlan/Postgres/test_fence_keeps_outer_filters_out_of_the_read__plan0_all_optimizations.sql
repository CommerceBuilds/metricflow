test_name: test_fence_keeps_outer_filters_out_of_the_read
test_filename: test_span_rendering.py
docstring:
  The read ends in `OFFSET 0`, and a flag filter stays outside it.

  Both flags are read in one plan, so the read is shared and each branch filters it from outside.
sql_engine: Postgres
---
-- Combine Aggregated Outputs
-- Write to DataTable
WITH rss_90002_cte AS NOT MATERIALIZED (
  -- Read Elements From Semantic Model 'inventory_spans'
  SELECT
    on_hand_units AS __ending_units
    , on_hand_units AS __beginning_units
    , DATE_TRUNC('day', ds) AS ds__day
    , span_is_last AS inventory_span__span_is_last
    , span_is_first AS inventory_span__span_is_first
  FROM (
    WITH span_periods AS (SELECT d.fiscal_month AS p_key, MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days, ROW_NUMBER() OVER (ORDER BY MIN(d.ds)) AS p_no FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE) GROUP BY d.fiscal_month), span_day_periods AS (SELECT d.ds AS p_day, p.p_no FROM span_test.mf_time_spine d JOIN span_periods p ON p.p_key = d.fiscal_month WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE)) SELECT span.*, sd.*, LEAST(COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1), p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM (SELECT * FROM span_test.fct_inventory_spans span WHERE span.valid_from <= CAST(:range_to AS DATE) AND (span.valid_to > CAST(:range_from AS DATE) OR span.valid_to IS NULL) AND span.valid_from < COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1)) span JOIN span_day_periods lo ON lo.p_day = GREATEST(span.valid_from, CAST(:range_from AS DATE)) JOIN span_day_periods hi ON hi.p_day = LEAST(COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) - 1, CAST(:range_to AS DATE)) CROSS JOIN LATERAL generate_series(lo.p_no, hi.p_no) AS g(p_no) JOIN span_periods p ON p.p_no = g.p_no JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first OFFSET 0
  ) inventory_spans_src_90000
)

SELECT
  COALESCE(subq_90041.metric_time__fiscal_month, subq_90049.metric_time__fiscal_month) AS metric_time__fiscal_month
  , COALESCE(MAX(subq_90041.ending_units), 0) AS ending_units
  , COALESCE(MAX(subq_90049.beginning_units), 0) AS beginning_units
FROM (
  -- Compute Metrics via Expressions
  SELECT
    metric_time__fiscal_month
    , COALESCE(__ending_units, 0) AS ending_units
  FROM (
    -- Constrain Output with WHERE
    -- Select: ['__ending_units', 'metric_time__fiscal_month']
    -- Aggregate Inputs for Simple Metrics
    SELECT
      metric_time__fiscal_month
      , SUM(ending_units) AS __ending_units
    FROM (
      -- Metric Time Dimension 'ds'
      -- Join to Custom Granularity Dataset
      -- Select: ['__ending_units', 'inventory_span__span_is_last', 'metric_time__fiscal_month']
      SELECT
        subq_90035.fiscal_month AS metric_time__fiscal_month
        , rss_90002_cte.inventory_span__span_is_last AS inventory_span__span_is_last
        , rss_90002_cte.__ending_units AS ending_units
      FROM rss_90002_cte
      LEFT OUTER JOIN
        span_test.mf_time_spine subq_90035
      ON
        rss_90002_cte.ds__day = subq_90035.ds
    ) subq_90037
    WHERE inventory_span__span_is_last = 1
    GROUP BY
      metric_time__fiscal_month
  ) subq_90040
) subq_90041
FULL OUTER JOIN (
  -- Compute Metrics via Expressions
  SELECT
    metric_time__fiscal_month
    , COALESCE(__beginning_units, 0) AS beginning_units
  FROM (
    -- Constrain Output with WHERE
    -- Select: ['__beginning_units', 'metric_time__fiscal_month']
    -- Aggregate Inputs for Simple Metrics
    SELECT
      metric_time__fiscal_month
      , SUM(beginning_units) AS __beginning_units
    FROM (
      -- Metric Time Dimension 'ds'
      -- Join to Custom Granularity Dataset
      -- Select: ['__beginning_units', 'inventory_span__span_is_first', 'metric_time__fiscal_month']
      SELECT
        subq_90043.fiscal_month AS metric_time__fiscal_month
        , rss_90002_cte.inventory_span__span_is_first AS inventory_span__span_is_first
        , rss_90002_cte.__beginning_units AS beginning_units
      FROM rss_90002_cte
      LEFT OUTER JOIN
        span_test.mf_time_spine subq_90043
      ON
        rss_90002_cte.ds__day = subq_90043.ds
    ) subq_90045
    WHERE inventory_span__span_is_first = 1
    GROUP BY
      metric_time__fiscal_month
  ) subq_90048
) subq_90049
ON
  subq_90041.metric_time__fiscal_month = subq_90049.metric_time__fiscal_month
GROUP BY
  COALESCE(subq_90041.metric_time__fiscal_month, subq_90049.metric_time__fiscal_month)
