test_name: test_span_read_at_a_fiscal_grain
test_filename: test_span_rendering.py
docstring:
  A span model by a custom grain: the range's periods numbered from the spine, each span expanded by number.
sql_engine: Postgres
---
-- Write to DataTable
SELECT
  subq_90006.metric_time__fiscal_month
  , subq_90006.unit_days
FROM (
  -- Compute Metrics via Expressions
  SELECT
    subq_90005.metric_time__fiscal_month
    , subq_90005.__unit_days AS unit_days
  FROM (
    -- Aggregate Inputs for Simple Metrics
    SELECT
      subq_90004.metric_time__fiscal_month
      , SUM(subq_90004.__unit_days) AS __unit_days
    FROM (
      -- Select: ['__unit_days', 'metric_time__fiscal_month']
      SELECT
        subq_90003.metric_time__fiscal_month
        , subq_90003.__unit_days
      FROM (
        -- Select: ['__unit_days', 'metric_time__fiscal_month']
        SELECT
          subq_90002.metric_time__fiscal_month
          , subq_90002.__unit_days
        FROM (
          -- Metric Time Dimension 'ds'
          -- Join to Custom Granularity Dataset
          SELECT
            subq_90000.ds__day AS ds__day
            , subq_90000.ds__week AS ds__week
            , subq_90000.ds__month AS ds__month
            , subq_90000.ds__quarter AS ds__quarter
            , subq_90000.ds__year AS ds__year
            , subq_90000.ds__extract_year AS ds__extract_year
            , subq_90000.ds__extract_quarter AS ds__extract_quarter
            , subq_90000.ds__extract_month AS ds__extract_month
            , subq_90000.ds__extract_day AS ds__extract_day
            , subq_90000.ds__extract_dow AS ds__extract_dow
            , subq_90000.ds__extract_doy AS ds__extract_doy
            , subq_90000.span_from__day AS span_from__day
            , subq_90000.span_from__week AS span_from__week
            , subq_90000.span_from__month AS span_from__month
            , subq_90000.span_from__quarter AS span_from__quarter
            , subq_90000.span_from__year AS span_from__year
            , subq_90000.span_from__extract_year AS span_from__extract_year
            , subq_90000.span_from__extract_quarter AS span_from__extract_quarter
            , subq_90000.span_from__extract_month AS span_from__extract_month
            , subq_90000.span_from__extract_day AS span_from__extract_day
            , subq_90000.span_from__extract_dow AS span_from__extract_dow
            , subq_90000.span_from__extract_doy AS span_from__extract_doy
            , subq_90000.span_to__day AS span_to__day
            , subq_90000.span_to__week AS span_to__week
            , subq_90000.span_to__month AS span_to__month
            , subq_90000.span_to__quarter AS span_to__quarter
            , subq_90000.span_to__year AS span_to__year
            , subq_90000.span_to__extract_year AS span_to__extract_year
            , subq_90000.span_to__extract_quarter AS span_to__extract_quarter
            , subq_90000.span_to__extract_month AS span_to__extract_month
            , subq_90000.span_to__extract_day AS span_to__extract_day
            , subq_90000.span_to__extract_dow AS span_to__extract_dow
            , subq_90000.span_to__extract_doy AS span_to__extract_doy
            , subq_90000.inventory_span__ds__day AS inventory_span__ds__day
            , subq_90000.inventory_span__ds__week AS inventory_span__ds__week
            , subq_90000.inventory_span__ds__month AS inventory_span__ds__month
            , subq_90000.inventory_span__ds__quarter AS inventory_span__ds__quarter
            , subq_90000.inventory_span__ds__year AS inventory_span__ds__year
            , subq_90000.inventory_span__ds__extract_year AS inventory_span__ds__extract_year
            , subq_90000.inventory_span__ds__extract_quarter AS inventory_span__ds__extract_quarter
            , subq_90000.inventory_span__ds__extract_month AS inventory_span__ds__extract_month
            , subq_90000.inventory_span__ds__extract_day AS inventory_span__ds__extract_day
            , subq_90000.inventory_span__ds__extract_dow AS inventory_span__ds__extract_dow
            , subq_90000.inventory_span__ds__extract_doy AS inventory_span__ds__extract_doy
            , subq_90000.inventory_span__span_from__day AS inventory_span__span_from__day
            , subq_90000.inventory_span__span_from__week AS inventory_span__span_from__week
            , subq_90000.inventory_span__span_from__month AS inventory_span__span_from__month
            , subq_90000.inventory_span__span_from__quarter AS inventory_span__span_from__quarter
            , subq_90000.inventory_span__span_from__year AS inventory_span__span_from__year
            , subq_90000.inventory_span__span_from__extract_year AS inventory_span__span_from__extract_year
            , subq_90000.inventory_span__span_from__extract_quarter AS inventory_span__span_from__extract_quarter
            , subq_90000.inventory_span__span_from__extract_month AS inventory_span__span_from__extract_month
            , subq_90000.inventory_span__span_from__extract_day AS inventory_span__span_from__extract_day
            , subq_90000.inventory_span__span_from__extract_dow AS inventory_span__span_from__extract_dow
            , subq_90000.inventory_span__span_from__extract_doy AS inventory_span__span_from__extract_doy
            , subq_90000.inventory_span__span_to__day AS inventory_span__span_to__day
            , subq_90000.inventory_span__span_to__week AS inventory_span__span_to__week
            , subq_90000.inventory_span__span_to__month AS inventory_span__span_to__month
            , subq_90000.inventory_span__span_to__quarter AS inventory_span__span_to__quarter
            , subq_90000.inventory_span__span_to__year AS inventory_span__span_to__year
            , subq_90000.inventory_span__span_to__extract_year AS inventory_span__span_to__extract_year
            , subq_90000.inventory_span__span_to__extract_quarter AS inventory_span__span_to__extract_quarter
            , subq_90000.inventory_span__span_to__extract_month AS inventory_span__span_to__extract_month
            , subq_90000.inventory_span__span_to__extract_day AS inventory_span__span_to__extract_day
            , subq_90000.inventory_span__span_to__extract_dow AS inventory_span__span_to__extract_dow
            , subq_90000.inventory_span__span_to__extract_doy AS inventory_span__span_to__extract_doy
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
            , subq_90000.location AS location
            , subq_90000.inventory_span__location AS inventory_span__location
            , subq_90000.span_is_last AS span_is_last
            , subq_90000.span_is_first AS span_is_first
            , subq_90000.inventory_span__span_is_last AS inventory_span__span_is_last
            , subq_90000.inventory_span__span_is_first AS inventory_span__span_is_first
            , subq_90000.__unit_days AS __unit_days
            , subq_90000.__ending_units AS __ending_units
            , subq_90000.__beginning_units AS __beginning_units
            , subq_90001.fiscal_month AS metric_time__fiscal_month
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
              WITH span_periods AS (SELECT d.fiscal_month AS p_key, MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days, ROW_NUMBER() OVER (ORDER BY MIN(d.ds)) AS p_no FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE) GROUP BY d.fiscal_month), span_day_periods AS (SELECT d.ds AS p_day, p.p_no FROM span_test.mf_time_spine d JOIN span_periods p ON p.p_key = d.fiscal_month WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE)) SELECT span.*, sd.*, LEAST(span.valid_to, p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND span.valid_to > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND span.valid_to > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM (SELECT * FROM span_test.fct_inventory_spans span WHERE span.valid_from <= CAST(:range_to AS DATE) AND span.valid_to > CAST(:range_from AS DATE) AND span.valid_from < span.valid_to) span JOIN span_day_periods lo ON lo.p_day = GREATEST(span.valid_from, CAST(:range_from AS DATE)) JOIN span_day_periods hi ON hi.p_day = LEAST(span.valid_to - 1, CAST(:range_to AS DATE)) CROSS JOIN LATERAL generate_series(lo.p_no, hi.p_no) AS g(p_no) JOIN span_periods p ON p.p_no = g.p_no JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first OFFSET 0
            ) inventory_spans_src_90000
          ) subq_90000
          LEFT OUTER JOIN
            span_test.mf_time_spine subq_90001
          ON
            subq_90000.ds__day = subq_90001.ds
        ) subq_90002
      ) subq_90003
    ) subq_90004
    GROUP BY
      subq_90004.metric_time__fiscal_month
  ) subq_90005
) subq_90006
