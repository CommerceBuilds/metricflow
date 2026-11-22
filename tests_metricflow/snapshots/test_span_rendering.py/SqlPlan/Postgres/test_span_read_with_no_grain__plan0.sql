test_name: test_span_read_with_no_grain
test_filename: test_span_rendering.py
docstring:
  A span model with no time grain: the whole range as one period.
sql_engine: Postgres
---
-- Write to DataTable
SELECT
  subq_90005.location
  , subq_90005.unit_days
FROM (
  -- Compute Metrics via Expressions
  SELECT
    subq_90004.location
    , subq_90004.__unit_days AS unit_days
  FROM (
    -- Aggregate Inputs for Simple Metrics
    SELECT
      subq_90003.location
      , SUM(subq_90003.__unit_days) AS __unit_days
    FROM (
      -- Select: ['__unit_days', 'location']
      SELECT
        subq_90002.location
        , subq_90002.__unit_days
      FROM (
        -- Select: ['__unit_days', 'location']
        SELECT
          subq_90001.location
          , subq_90001.__unit_days
        FROM (
          -- Metric Time Dimension 'ds'
          SELECT
            subq_90000.ds__day
            , subq_90000.ds__week
            , subq_90000.ds__month
            , subq_90000.ds__quarter
            , subq_90000.ds__year
            , subq_90000.ds__extract_year
            , subq_90000.ds__extract_quarter
            , subq_90000.ds__extract_month
            , subq_90000.ds__extract_day
            , subq_90000.ds__extract_dow
            , subq_90000.ds__extract_doy
            , subq_90000.span_from__day
            , subq_90000.span_from__week
            , subq_90000.span_from__month
            , subq_90000.span_from__quarter
            , subq_90000.span_from__year
            , subq_90000.span_from__extract_year
            , subq_90000.span_from__extract_quarter
            , subq_90000.span_from__extract_month
            , subq_90000.span_from__extract_day
            , subq_90000.span_from__extract_dow
            , subq_90000.span_from__extract_doy
            , subq_90000.span_to__day
            , subq_90000.span_to__week
            , subq_90000.span_to__month
            , subq_90000.span_to__quarter
            , subq_90000.span_to__year
            , subq_90000.span_to__extract_year
            , subq_90000.span_to__extract_quarter
            , subq_90000.span_to__extract_month
            , subq_90000.span_to__extract_day
            , subq_90000.span_to__extract_dow
            , subq_90000.span_to__extract_doy
            , subq_90000.inventory_span__ds__day
            , subq_90000.inventory_span__ds__week
            , subq_90000.inventory_span__ds__month
            , subq_90000.inventory_span__ds__quarter
            , subq_90000.inventory_span__ds__year
            , subq_90000.inventory_span__ds__extract_year
            , subq_90000.inventory_span__ds__extract_quarter
            , subq_90000.inventory_span__ds__extract_month
            , subq_90000.inventory_span__ds__extract_day
            , subq_90000.inventory_span__ds__extract_dow
            , subq_90000.inventory_span__ds__extract_doy
            , subq_90000.inventory_span__span_from__day
            , subq_90000.inventory_span__span_from__week
            , subq_90000.inventory_span__span_from__month
            , subq_90000.inventory_span__span_from__quarter
            , subq_90000.inventory_span__span_from__year
            , subq_90000.inventory_span__span_from__extract_year
            , subq_90000.inventory_span__span_from__extract_quarter
            , subq_90000.inventory_span__span_from__extract_month
            , subq_90000.inventory_span__span_from__extract_day
            , subq_90000.inventory_span__span_from__extract_dow
            , subq_90000.inventory_span__span_from__extract_doy
            , subq_90000.inventory_span__span_to__day
            , subq_90000.inventory_span__span_to__week
            , subq_90000.inventory_span__span_to__month
            , subq_90000.inventory_span__span_to__quarter
            , subq_90000.inventory_span__span_to__year
            , subq_90000.inventory_span__span_to__extract_year
            , subq_90000.inventory_span__span_to__extract_quarter
            , subq_90000.inventory_span__span_to__extract_month
            , subq_90000.inventory_span__span_to__extract_day
            , subq_90000.inventory_span__span_to__extract_dow
            , subq_90000.inventory_span__span_to__extract_doy
            , subq_90000.ds__day AS metric_time__day
            , subq_90000.ds__week AS metric_time__week
            , subq_90000.ds__month AS metric_time__month
            , subq_90000.ds__quarter AS metric_time__quarter
            , subq_90000.ds__year AS metric_time__year
            , subq_90000.ds__extract_year AS metric_time__extract_year
            , subq_90000.ds__extract_quarter AS metric_time__extract_quarter
            , subq_90000.ds__extract_month AS metric_time__extract_month
            , subq_90000.ds__extract_day AS metric_time__extract_day
            , subq_90000.ds__extract_dow AS metric_time__extract_dow
            , subq_90000.ds__extract_doy AS metric_time__extract_doy
            , subq_90000.location
            , subq_90000.inventory_span__location
            , subq_90000.span_is_last
            , subq_90000.span_is_first
            , subq_90000.inventory_span__span_is_last
            , subq_90000.inventory_span__span_is_first
            , subq_90000.__unit_days
            , subq_90000.__ending_units
            , subq_90000.__beginning_units
          FROM (
            -- Read Elements From Semantic Model 'inventory_spans'
            SELECT
              on_hand_units * span_days AS __unit_days
              , inventory_spans_src_90000.on_hand_units AS __ending_units
              , inventory_spans_src_90000.on_hand_units AS __beginning_units
              , DATE_TRUNC('day', inventory_spans_src_90000.ds) AS ds__day
              , DATE_TRUNC('week', inventory_spans_src_90000.ds) AS ds__week
              , DATE_TRUNC('month', inventory_spans_src_90000.ds) AS ds__month
              , DATE_TRUNC('quarter', inventory_spans_src_90000.ds) AS ds__quarter
              , DATE_TRUNC('year', inventory_spans_src_90000.ds) AS ds__year
              , EXTRACT(year FROM inventory_spans_src_90000.ds) AS ds__extract_year
              , EXTRACT(quarter FROM inventory_spans_src_90000.ds) AS ds__extract_quarter
              , EXTRACT(month FROM inventory_spans_src_90000.ds) AS ds__extract_month
              , EXTRACT(day FROM inventory_spans_src_90000.ds) AS ds__extract_day
              , EXTRACT(isodow FROM inventory_spans_src_90000.ds) AS ds__extract_dow
              , EXTRACT(doy FROM inventory_spans_src_90000.ds) AS ds__extract_doy
              , inventory_spans_src_90000.span_is_last
              , inventory_spans_src_90000.span_is_first
              , inventory_spans_src_90000.valid_from AS span_from__day
              , DATE_TRUNC('week', inventory_spans_src_90000.valid_from) AS span_from__week
              , DATE_TRUNC('month', inventory_spans_src_90000.valid_from) AS span_from__month
              , DATE_TRUNC('quarter', inventory_spans_src_90000.valid_from) AS span_from__quarter
              , DATE_TRUNC('year', inventory_spans_src_90000.valid_from) AS span_from__year
              , EXTRACT(year FROM inventory_spans_src_90000.valid_from) AS span_from__extract_year
              , EXTRACT(quarter FROM inventory_spans_src_90000.valid_from) AS span_from__extract_quarter
              , EXTRACT(month FROM inventory_spans_src_90000.valid_from) AS span_from__extract_month
              , EXTRACT(day FROM inventory_spans_src_90000.valid_from) AS span_from__extract_day
              , EXTRACT(isodow FROM inventory_spans_src_90000.valid_from) AS span_from__extract_dow
              , EXTRACT(doy FROM inventory_spans_src_90000.valid_from) AS span_from__extract_doy
              , inventory_spans_src_90000.valid_to AS span_to__day
              , DATE_TRUNC('week', inventory_spans_src_90000.valid_to) AS span_to__week
              , DATE_TRUNC('month', inventory_spans_src_90000.valid_to) AS span_to__month
              , DATE_TRUNC('quarter', inventory_spans_src_90000.valid_to) AS span_to__quarter
              , DATE_TRUNC('year', inventory_spans_src_90000.valid_to) AS span_to__year
              , EXTRACT(year FROM inventory_spans_src_90000.valid_to) AS span_to__extract_year
              , EXTRACT(quarter FROM inventory_spans_src_90000.valid_to) AS span_to__extract_quarter
              , EXTRACT(month FROM inventory_spans_src_90000.valid_to) AS span_to__extract_month
              , EXTRACT(day FROM inventory_spans_src_90000.valid_to) AS span_to__extract_day
              , EXTRACT(isodow FROM inventory_spans_src_90000.valid_to) AS span_to__extract_dow
              , EXTRACT(doy FROM inventory_spans_src_90000.valid_to) AS span_to__extract_doy
              , DATE_TRUNC('day', inventory_spans_src_90000.ds) AS inventory_span__ds__day
              , DATE_TRUNC('week', inventory_spans_src_90000.ds) AS inventory_span__ds__week
              , DATE_TRUNC('month', inventory_spans_src_90000.ds) AS inventory_span__ds__month
              , DATE_TRUNC('quarter', inventory_spans_src_90000.ds) AS inventory_span__ds__quarter
              , DATE_TRUNC('year', inventory_spans_src_90000.ds) AS inventory_span__ds__year
              , EXTRACT(year FROM inventory_spans_src_90000.ds) AS inventory_span__ds__extract_year
              , EXTRACT(quarter FROM inventory_spans_src_90000.ds) AS inventory_span__ds__extract_quarter
              , EXTRACT(month FROM inventory_spans_src_90000.ds) AS inventory_span__ds__extract_month
              , EXTRACT(day FROM inventory_spans_src_90000.ds) AS inventory_span__ds__extract_day
              , EXTRACT(isodow FROM inventory_spans_src_90000.ds) AS inventory_span__ds__extract_dow
              , EXTRACT(doy FROM inventory_spans_src_90000.ds) AS inventory_span__ds__extract_doy
              , inventory_spans_src_90000.span_is_last AS inventory_span__span_is_last
              , inventory_spans_src_90000.span_is_first AS inventory_span__span_is_first
              , inventory_spans_src_90000.valid_from AS inventory_span__span_from__day
              , DATE_TRUNC('week', inventory_spans_src_90000.valid_from) AS inventory_span__span_from__week
              , DATE_TRUNC('month', inventory_spans_src_90000.valid_from) AS inventory_span__span_from__month
              , DATE_TRUNC('quarter', inventory_spans_src_90000.valid_from) AS inventory_span__span_from__quarter
              , DATE_TRUNC('year', inventory_spans_src_90000.valid_from) AS inventory_span__span_from__year
              , EXTRACT(year FROM inventory_spans_src_90000.valid_from) AS inventory_span__span_from__extract_year
              , EXTRACT(quarter FROM inventory_spans_src_90000.valid_from) AS inventory_span__span_from__extract_quarter
              , EXTRACT(month FROM inventory_spans_src_90000.valid_from) AS inventory_span__span_from__extract_month
              , EXTRACT(day FROM inventory_spans_src_90000.valid_from) AS inventory_span__span_from__extract_day
              , EXTRACT(isodow FROM inventory_spans_src_90000.valid_from) AS inventory_span__span_from__extract_dow
              , EXTRACT(doy FROM inventory_spans_src_90000.valid_from) AS inventory_span__span_from__extract_doy
              , inventory_spans_src_90000.valid_to AS inventory_span__span_to__day
              , DATE_TRUNC('week', inventory_spans_src_90000.valid_to) AS inventory_span__span_to__week
              , DATE_TRUNC('month', inventory_spans_src_90000.valid_to) AS inventory_span__span_to__month
              , DATE_TRUNC('quarter', inventory_spans_src_90000.valid_to) AS inventory_span__span_to__quarter
              , DATE_TRUNC('year', inventory_spans_src_90000.valid_to) AS inventory_span__span_to__year
              , EXTRACT(year FROM inventory_spans_src_90000.valid_to) AS inventory_span__span_to__extract_year
              , EXTRACT(quarter FROM inventory_spans_src_90000.valid_to) AS inventory_span__span_to__extract_quarter
              , EXTRACT(month FROM inventory_spans_src_90000.valid_to) AS inventory_span__span_to__extract_month
              , EXTRACT(day FROM inventory_spans_src_90000.valid_to) AS inventory_span__span_to__extract_day
              , EXTRACT(isodow FROM inventory_spans_src_90000.valid_to) AS inventory_span__span_to__extract_dow
              , EXTRACT(doy FROM inventory_spans_src_90000.valid_to) AS inventory_span__span_to__extract_doy
              , inventory_spans_src_90000.location_id AS location
              , inventory_spans_src_90000.location_id AS inventory_span__location
            FROM (
              SELECT span.*, sd.*, LEAST(COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1), p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM span_test.fct_inventory_spans span JOIN (SELECT MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE)) p ON TRUE JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first WHERE span.valid_from <= CAST(:range_to AS DATE) AND (span.valid_to > CAST(:range_from AS DATE) OR span.valid_to IS NULL)
            ) inventory_spans_src_90000
          ) subq_90000
        ) subq_90001
      ) subq_90002
    ) subq_90003
    GROUP BY
      subq_90003.location
  ) subq_90004
) subq_90005
