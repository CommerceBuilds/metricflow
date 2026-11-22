test_name: test_span_read_at_a_standard_grain
test_filename: test_span_rendering.py
docstring:
  A span model by week: each span expanded straight to its weeks' first days, joined on that day.
sql_engine: Postgres
---
-- Aggregate Inputs for Simple Metrics
-- Compute Metrics via Expressions
-- Write to DataTable
SELECT
  metric_time__week
  , SUM(__unit_days) AS unit_days
FROM (
  -- Read Elements From Semantic Model 'inventory_spans'
  -- Metric Time Dimension 'ds'
  -- Select: ['__unit_days', 'metric_time__week']
  -- Select: ['__unit_days', 'metric_time__week']
  SELECT
    DATE_TRUNC('week', ds) AS metric_time__week
    , on_hand_units * span_days AS __unit_days
  FROM (
    WITH span_periods AS (SELECT CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE) AS p_key, MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE) GROUP BY CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE)) SELECT span.*, sd.*, LEAST(COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1), p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM (SELECT * FROM span_test.fct_inventory_spans span WHERE span.valid_from <= CAST(:range_to AS DATE) AND (span.valid_to > CAST(:range_from AS DATE) OR span.valid_to IS NULL) AND span.valid_from < COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1)) span CROSS JOIN LATERAL generate_series(DATE_TRUNC('week', CAST(GREATEST(span.valid_from, CAST(:range_from AS DATE)) AS TIMESTAMP)), DATE_TRUNC('week', CAST(LEAST(COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) - 1, CAST(:range_to AS DATE)) AS TIMESTAMP)), INTERVAL '1 week') AS g(p_start) JOIN span_periods p ON p.p_key = CAST(g.p_start AS DATE) JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first OFFSET 0
  ) inventory_spans_src_90000
) subq_90009
GROUP BY
  metric_time__week
