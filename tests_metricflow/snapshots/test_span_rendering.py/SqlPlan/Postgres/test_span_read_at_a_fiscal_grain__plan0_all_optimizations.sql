test_name: test_span_read_at_a_fiscal_grain
test_filename: test_span_rendering.py
docstring:
  A span model by a custom grain: the range's periods numbered from the spine, each span expanded by number.
sql_engine: Postgres
---
-- Metric Time Dimension 'ds'
-- Join to Custom Granularity Dataset
-- Select: ['__unit_days', 'metric_time__fiscal_month']
-- Select: ['__unit_days', 'metric_time__fiscal_month']
-- Aggregate Inputs for Simple Metrics
-- Compute Metrics via Expressions
-- Write to DataTable
SELECT
  subq_90015.fiscal_month AS metric_time__fiscal_month
  , SUM(subq_90014.__unit_days) AS unit_days
FROM (
  -- Read Elements From Semantic Model 'inventory_spans'
  SELECT
    on_hand_units * span_days AS __unit_days
    , DATE_TRUNC('day', ds) AS ds__day
  FROM (
    WITH span_periods AS (SELECT d.fiscal_month AS p_key, MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days, ROW_NUMBER() OVER (ORDER BY MIN(d.ds)) AS p_no FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE) GROUP BY d.fiscal_month), span_day_periods AS (SELECT d.ds AS p_day, p.p_no FROM span_test.mf_time_spine d JOIN span_periods p ON p.p_key = d.fiscal_month WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE)) SELECT span.*, sd.*, LEAST(COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1), p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM (SELECT * FROM span_test.fct_inventory_spans span WHERE span.valid_from <= CAST(:range_to AS DATE) AND (span.valid_to > CAST(:range_from AS DATE) OR span.valid_to IS NULL) AND span.valid_from < COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1)) span JOIN span_day_periods lo ON lo.p_day = GREATEST(span.valid_from, CAST(:range_from AS DATE)) JOIN span_day_periods hi ON hi.p_day = LEAST(COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) - 1, CAST(:range_to AS DATE)) CROSS JOIN LATERAL generate_series(lo.p_no, hi.p_no) AS g(p_no) JOIN span_periods p ON p.p_no = g.p_no JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first OFFSET 0
  ) inventory_spans_src_90000
) subq_90014
LEFT OUTER JOIN
  span_test.mf_time_spine subq_90015
ON
  subq_90014.ds__day = subq_90015.ds
GROUP BY
  subq_90015.fiscal_month
