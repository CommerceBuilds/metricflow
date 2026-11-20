test_name: test_span_read_with_no_grain
test_filename: test_span_rendering.py
docstring:
  A span model with no time grain: the whole range as one period.
sql_engine: Postgres
---
-- Aggregate Inputs for Simple Metrics
-- Compute Metrics via Expressions
-- Write to DataTable
SELECT
  location
  , SUM(__unit_days) AS unit_days
FROM (
  -- Read Elements From Semantic Model 'inventory_spans'
  -- Metric Time Dimension 'ds'
  -- Select: ['__unit_days', 'location']
  -- Select: ['__unit_days', 'location']
  SELECT
    location_id AS location
    , on_hand_units * span_days AS __unit_days
  FROM (
    SELECT span.*, sd.*, LEAST(span.valid_to, p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND span.valid_to > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND span.valid_to > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM span_test.fct_inventory_spans span JOIN (SELECT MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE)) p ON span.valid_from <= p.p_last AND span.valid_to > p.p_first JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first WHERE span.valid_from <= CAST(:range_to AS DATE) AND span.valid_to > CAST(:range_from AS DATE)
  ) inventory_spans_src_90000
) subq_90009
GROUP BY
  location
