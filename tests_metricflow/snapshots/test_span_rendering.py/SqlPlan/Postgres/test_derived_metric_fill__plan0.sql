test_name: test_derived_metric_fill
test_filename: test_span_rendering.py
docstring:
  A derived metric with `config.meta.fill_nulls_with` fills in the select that combines metrics' outputs.
sql_engine: Postgres
---
-- Write to DataTable
SELECT
  subq_90026.metric_time__week
  , subq_90026.unit_change
  , subq_90026.unit_change_unfilled
  , subq_90026.received_units
FROM (
  -- Combine Aggregated Outputs
  SELECT
    COALESCE(subq_90015.metric_time__week, subq_90019.metric_time__week, subq_90025.metric_time__week) AS metric_time__week
    , COALESCE(MAX(subq_90015.unit_change), 0) AS unit_change
    , MAX(subq_90019.unit_change_unfilled) AS unit_change_unfilled
    , MAX(subq_90025.received_units) AS received_units
  FROM (
    -- Compute Metrics via Expressions
    SELECT
      subq_90014.metric_time__week
      , ending_units - beginning_units AS unit_change
    FROM (
      -- Combine Aggregated Outputs
      SELECT
        COALESCE(subq_90006.metric_time__week, subq_90013.metric_time__week) AS metric_time__week
        , MAX(subq_90006.ending_units) AS ending_units
        , MAX(subq_90013.beginning_units) AS beginning_units
      FROM (
        -- Compute Metrics via Expressions
        SELECT
          subq_90005.metric_time__week
          , subq_90005.__ending_units AS ending_units
        FROM (
          -- Aggregate Inputs for Simple Metrics
          SELECT
            subq_90004.metric_time__week
            , SUM(subq_90004.__ending_units) AS __ending_units
          FROM (
            -- Select: ['__ending_units', 'metric_time__week']
            SELECT
              subq_90003.metric_time__week
              , subq_90003.__ending_units
            FROM (
              -- Constrain Output with WHERE
              SELECT
                subq_90002.ending_units AS __ending_units
                , subq_90002.inventory_span__span_is_last
                , subq_90002.metric_time__week
              FROM (
                -- Select: ['__ending_units', 'inventory_span__span_is_last', 'metric_time__week']
                SELECT
                  subq_90001.metric_time__week
                  , subq_90001.inventory_span__span_is_last
                  , subq_90001.__ending_units AS ending_units
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
                      WITH span_periods AS (SELECT CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE) AS p_key, MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE) GROUP BY CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE)) SELECT span.*, sd.*, LEAST(span.valid_to, p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND span.valid_to > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND span.valid_to > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM (SELECT * FROM span_test.fct_inventory_spans span WHERE span.valid_from <= CAST(:range_to AS DATE) AND span.valid_to > CAST(:range_from AS DATE) AND span.valid_from < span.valid_to) span CROSS JOIN LATERAL generate_series(DATE_TRUNC('week', CAST(GREATEST(span.valid_from, CAST(:range_from AS DATE)) AS TIMESTAMP)), DATE_TRUNC('week', CAST(LEAST(span.valid_to - 1, CAST(:range_to AS DATE)) AS TIMESTAMP)), INTERVAL '1 week') AS g(p_start) JOIN span_periods p ON p.p_key = CAST(g.p_start AS DATE) JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first OFFSET 0
                    ) inventory_spans_src_90000
                  ) subq_90000
                ) subq_90001
              ) subq_90002
              WHERE inventory_span__span_is_last = 1
            ) subq_90003
          ) subq_90004
          GROUP BY
            subq_90004.metric_time__week
        ) subq_90005
      ) subq_90006
      FULL OUTER JOIN (
        -- Compute Metrics via Expressions
        SELECT
          subq_90012.metric_time__week
          , subq_90012.__beginning_units AS beginning_units
        FROM (
          -- Aggregate Inputs for Simple Metrics
          SELECT
            subq_90011.metric_time__week
            , SUM(subq_90011.__beginning_units) AS __beginning_units
          FROM (
            -- Select: ['__beginning_units', 'metric_time__week']
            SELECT
              subq_90010.metric_time__week
              , subq_90010.__beginning_units
            FROM (
              -- Constrain Output with WHERE
              SELECT
                subq_90009.beginning_units AS __beginning_units
                , subq_90009.inventory_span__span_is_first
                , subq_90009.metric_time__week
              FROM (
                -- Select: ['__beginning_units', 'inventory_span__span_is_first', 'metric_time__week']
                SELECT
                  subq_90008.metric_time__week
                  , subq_90008.inventory_span__span_is_first
                  , subq_90008.__beginning_units AS beginning_units
                FROM (
                  -- Metric Time Dimension 'ds'
                  SELECT
                    subq_90007.ds__day
                    , subq_90007.ds__week
                    , subq_90007.ds__month
                    , subq_90007.ds__quarter
                    , subq_90007.ds__year
                    , subq_90007.ds__extract_year
                    , subq_90007.ds__extract_quarter
                    , subq_90007.ds__extract_month
                    , subq_90007.ds__extract_day
                    , subq_90007.ds__extract_dow
                    , subq_90007.ds__extract_doy
                    , subq_90007.span_from__day
                    , subq_90007.span_from__week
                    , subq_90007.span_from__month
                    , subq_90007.span_from__quarter
                    , subq_90007.span_from__year
                    , subq_90007.span_from__extract_year
                    , subq_90007.span_from__extract_quarter
                    , subq_90007.span_from__extract_month
                    , subq_90007.span_from__extract_day
                    , subq_90007.span_from__extract_dow
                    , subq_90007.span_from__extract_doy
                    , subq_90007.span_to__day
                    , subq_90007.span_to__week
                    , subq_90007.span_to__month
                    , subq_90007.span_to__quarter
                    , subq_90007.span_to__year
                    , subq_90007.span_to__extract_year
                    , subq_90007.span_to__extract_quarter
                    , subq_90007.span_to__extract_month
                    , subq_90007.span_to__extract_day
                    , subq_90007.span_to__extract_dow
                    , subq_90007.span_to__extract_doy
                    , subq_90007.inventory_span__ds__day
                    , subq_90007.inventory_span__ds__week
                    , subq_90007.inventory_span__ds__month
                    , subq_90007.inventory_span__ds__quarter
                    , subq_90007.inventory_span__ds__year
                    , subq_90007.inventory_span__ds__extract_year
                    , subq_90007.inventory_span__ds__extract_quarter
                    , subq_90007.inventory_span__ds__extract_month
                    , subq_90007.inventory_span__ds__extract_day
                    , subq_90007.inventory_span__ds__extract_dow
                    , subq_90007.inventory_span__ds__extract_doy
                    , subq_90007.inventory_span__span_from__day
                    , subq_90007.inventory_span__span_from__week
                    , subq_90007.inventory_span__span_from__month
                    , subq_90007.inventory_span__span_from__quarter
                    , subq_90007.inventory_span__span_from__year
                    , subq_90007.inventory_span__span_from__extract_year
                    , subq_90007.inventory_span__span_from__extract_quarter
                    , subq_90007.inventory_span__span_from__extract_month
                    , subq_90007.inventory_span__span_from__extract_day
                    , subq_90007.inventory_span__span_from__extract_dow
                    , subq_90007.inventory_span__span_from__extract_doy
                    , subq_90007.inventory_span__span_to__day
                    , subq_90007.inventory_span__span_to__week
                    , subq_90007.inventory_span__span_to__month
                    , subq_90007.inventory_span__span_to__quarter
                    , subq_90007.inventory_span__span_to__year
                    , subq_90007.inventory_span__span_to__extract_year
                    , subq_90007.inventory_span__span_to__extract_quarter
                    , subq_90007.inventory_span__span_to__extract_month
                    , subq_90007.inventory_span__span_to__extract_day
                    , subq_90007.inventory_span__span_to__extract_dow
                    , subq_90007.inventory_span__span_to__extract_doy
                    , subq_90007.ds__day AS metric_time__day
                    , subq_90007.ds__week AS metric_time__week
                    , subq_90007.ds__month AS metric_time__month
                    , subq_90007.ds__quarter AS metric_time__quarter
                    , subq_90007.ds__year AS metric_time__year
                    , subq_90007.ds__extract_year AS metric_time__extract_year
                    , subq_90007.ds__extract_quarter AS metric_time__extract_quarter
                    , subq_90007.ds__extract_month AS metric_time__extract_month
                    , subq_90007.ds__extract_day AS metric_time__extract_day
                    , subq_90007.ds__extract_dow AS metric_time__extract_dow
                    , subq_90007.ds__extract_doy AS metric_time__extract_doy
                    , subq_90007.location
                    , subq_90007.inventory_span__location
                    , subq_90007.span_is_last
                    , subq_90007.span_is_first
                    , subq_90007.inventory_span__span_is_last
                    , subq_90007.inventory_span__span_is_first
                    , subq_90007.__unit_days
                    , subq_90007.__ending_units
                    , subq_90007.__beginning_units
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
                      WITH span_periods AS (SELECT CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE) AS p_key, MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE) GROUP BY CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE)) SELECT span.*, sd.*, LEAST(span.valid_to, p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND span.valid_to > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND span.valid_to > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM (SELECT * FROM span_test.fct_inventory_spans span WHERE span.valid_from <= CAST(:range_to AS DATE) AND span.valid_to > CAST(:range_from AS DATE) AND span.valid_from < span.valid_to) span CROSS JOIN LATERAL generate_series(DATE_TRUNC('week', CAST(GREATEST(span.valid_from, CAST(:range_from AS DATE)) AS TIMESTAMP)), DATE_TRUNC('week', CAST(LEAST(span.valid_to - 1, CAST(:range_to AS DATE)) AS TIMESTAMP)), INTERVAL '1 week') AS g(p_start) JOIN span_periods p ON p.p_key = CAST(g.p_start AS DATE) JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first OFFSET 0
                    ) inventory_spans_src_90000
                  ) subq_90007
                ) subq_90008
              ) subq_90009
              WHERE inventory_span__span_is_first = 1
            ) subq_90010
          ) subq_90011
          GROUP BY
            subq_90011.metric_time__week
        ) subq_90012
      ) subq_90013
      ON
        subq_90006.metric_time__week = subq_90013.metric_time__week
      GROUP BY
        COALESCE(subq_90006.metric_time__week, subq_90013.metric_time__week)
    ) subq_90014
  ) subq_90015
  FULL OUTER JOIN (
    -- Compute Metrics via Expressions
    SELECT
      subq_90018.metric_time__week
      , ending_units - beginning_units AS unit_change_unfilled
    FROM (
      -- Combine Aggregated Outputs
      SELECT
        COALESCE(subq_90016.metric_time__week, subq_90017.metric_time__week) AS metric_time__week
        , MAX(subq_90016.ending_units) AS ending_units
        , MAX(subq_90017.beginning_units) AS beginning_units
      FROM (
        -- Compute Metrics via Expressions
        SELECT
          subq_90005.metric_time__week
          , subq_90005.__ending_units AS ending_units
        FROM (
          -- Aggregate Inputs for Simple Metrics
          SELECT
            subq_90004.metric_time__week
            , SUM(subq_90004.__ending_units) AS __ending_units
          FROM (
            -- Select: ['__ending_units', 'metric_time__week']
            SELECT
              subq_90003.metric_time__week
              , subq_90003.__ending_units
            FROM (
              -- Constrain Output with WHERE
              SELECT
                subq_90002.ending_units AS __ending_units
                , subq_90002.inventory_span__span_is_last
                , subq_90002.metric_time__week
              FROM (
                -- Select: ['__ending_units', 'inventory_span__span_is_last', 'metric_time__week']
                SELECT
                  subq_90001.metric_time__week
                  , subq_90001.inventory_span__span_is_last
                  , subq_90001.__ending_units AS ending_units
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
                      WITH span_periods AS (SELECT CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE) AS p_key, MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE) GROUP BY CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE)) SELECT span.*, sd.*, LEAST(span.valid_to, p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND span.valid_to > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND span.valid_to > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM (SELECT * FROM span_test.fct_inventory_spans span WHERE span.valid_from <= CAST(:range_to AS DATE) AND span.valid_to > CAST(:range_from AS DATE) AND span.valid_from < span.valid_to) span CROSS JOIN LATERAL generate_series(DATE_TRUNC('week', CAST(GREATEST(span.valid_from, CAST(:range_from AS DATE)) AS TIMESTAMP)), DATE_TRUNC('week', CAST(LEAST(span.valid_to - 1, CAST(:range_to AS DATE)) AS TIMESTAMP)), INTERVAL '1 week') AS g(p_start) JOIN span_periods p ON p.p_key = CAST(g.p_start AS DATE) JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first OFFSET 0
                    ) inventory_spans_src_90000
                  ) subq_90000
                ) subq_90001
              ) subq_90002
              WHERE inventory_span__span_is_last = 1
            ) subq_90003
          ) subq_90004
          GROUP BY
            subq_90004.metric_time__week
        ) subq_90005
      ) subq_90016
      FULL OUTER JOIN (
        -- Compute Metrics via Expressions
        SELECT
          subq_90012.metric_time__week
          , subq_90012.__beginning_units AS beginning_units
        FROM (
          -- Aggregate Inputs for Simple Metrics
          SELECT
            subq_90011.metric_time__week
            , SUM(subq_90011.__beginning_units) AS __beginning_units
          FROM (
            -- Select: ['__beginning_units', 'metric_time__week']
            SELECT
              subq_90010.metric_time__week
              , subq_90010.__beginning_units
            FROM (
              -- Constrain Output with WHERE
              SELECT
                subq_90009.beginning_units AS __beginning_units
                , subq_90009.inventory_span__span_is_first
                , subq_90009.metric_time__week
              FROM (
                -- Select: ['__beginning_units', 'inventory_span__span_is_first', 'metric_time__week']
                SELECT
                  subq_90008.metric_time__week
                  , subq_90008.inventory_span__span_is_first
                  , subq_90008.__beginning_units AS beginning_units
                FROM (
                  -- Metric Time Dimension 'ds'
                  SELECT
                    subq_90007.ds__day
                    , subq_90007.ds__week
                    , subq_90007.ds__month
                    , subq_90007.ds__quarter
                    , subq_90007.ds__year
                    , subq_90007.ds__extract_year
                    , subq_90007.ds__extract_quarter
                    , subq_90007.ds__extract_month
                    , subq_90007.ds__extract_day
                    , subq_90007.ds__extract_dow
                    , subq_90007.ds__extract_doy
                    , subq_90007.span_from__day
                    , subq_90007.span_from__week
                    , subq_90007.span_from__month
                    , subq_90007.span_from__quarter
                    , subq_90007.span_from__year
                    , subq_90007.span_from__extract_year
                    , subq_90007.span_from__extract_quarter
                    , subq_90007.span_from__extract_month
                    , subq_90007.span_from__extract_day
                    , subq_90007.span_from__extract_dow
                    , subq_90007.span_from__extract_doy
                    , subq_90007.span_to__day
                    , subq_90007.span_to__week
                    , subq_90007.span_to__month
                    , subq_90007.span_to__quarter
                    , subq_90007.span_to__year
                    , subq_90007.span_to__extract_year
                    , subq_90007.span_to__extract_quarter
                    , subq_90007.span_to__extract_month
                    , subq_90007.span_to__extract_day
                    , subq_90007.span_to__extract_dow
                    , subq_90007.span_to__extract_doy
                    , subq_90007.inventory_span__ds__day
                    , subq_90007.inventory_span__ds__week
                    , subq_90007.inventory_span__ds__month
                    , subq_90007.inventory_span__ds__quarter
                    , subq_90007.inventory_span__ds__year
                    , subq_90007.inventory_span__ds__extract_year
                    , subq_90007.inventory_span__ds__extract_quarter
                    , subq_90007.inventory_span__ds__extract_month
                    , subq_90007.inventory_span__ds__extract_day
                    , subq_90007.inventory_span__ds__extract_dow
                    , subq_90007.inventory_span__ds__extract_doy
                    , subq_90007.inventory_span__span_from__day
                    , subq_90007.inventory_span__span_from__week
                    , subq_90007.inventory_span__span_from__month
                    , subq_90007.inventory_span__span_from__quarter
                    , subq_90007.inventory_span__span_from__year
                    , subq_90007.inventory_span__span_from__extract_year
                    , subq_90007.inventory_span__span_from__extract_quarter
                    , subq_90007.inventory_span__span_from__extract_month
                    , subq_90007.inventory_span__span_from__extract_day
                    , subq_90007.inventory_span__span_from__extract_dow
                    , subq_90007.inventory_span__span_from__extract_doy
                    , subq_90007.inventory_span__span_to__day
                    , subq_90007.inventory_span__span_to__week
                    , subq_90007.inventory_span__span_to__month
                    , subq_90007.inventory_span__span_to__quarter
                    , subq_90007.inventory_span__span_to__year
                    , subq_90007.inventory_span__span_to__extract_year
                    , subq_90007.inventory_span__span_to__extract_quarter
                    , subq_90007.inventory_span__span_to__extract_month
                    , subq_90007.inventory_span__span_to__extract_day
                    , subq_90007.inventory_span__span_to__extract_dow
                    , subq_90007.inventory_span__span_to__extract_doy
                    , subq_90007.ds__day AS metric_time__day
                    , subq_90007.ds__week AS metric_time__week
                    , subq_90007.ds__month AS metric_time__month
                    , subq_90007.ds__quarter AS metric_time__quarter
                    , subq_90007.ds__year AS metric_time__year
                    , subq_90007.ds__extract_year AS metric_time__extract_year
                    , subq_90007.ds__extract_quarter AS metric_time__extract_quarter
                    , subq_90007.ds__extract_month AS metric_time__extract_month
                    , subq_90007.ds__extract_day AS metric_time__extract_day
                    , subq_90007.ds__extract_dow AS metric_time__extract_dow
                    , subq_90007.ds__extract_doy AS metric_time__extract_doy
                    , subq_90007.location
                    , subq_90007.inventory_span__location
                    , subq_90007.span_is_last
                    , subq_90007.span_is_first
                    , subq_90007.inventory_span__span_is_last
                    , subq_90007.inventory_span__span_is_first
                    , subq_90007.__unit_days
                    , subq_90007.__ending_units
                    , subq_90007.__beginning_units
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
                      WITH span_periods AS (SELECT CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE) AS p_key, MIN(d.ds) AS p_first, MAX(d.ds) AS p_last, COUNT(*) AS p_days FROM span_test.mf_time_spine d WHERE d.ds >= CAST(:range_from AS DATE) AND d.ds <= CAST(:range_to AS DATE) GROUP BY CAST(DATE_TRUNC('week', CAST(d.ds AS TIMESTAMP)) AS DATE)) SELECT span.*, sd.*, LEAST(span.valid_to, p.p_last + 1) - GREATEST(span.valid_from, p.p_first) AS span_days, CASE WHEN span.valid_from <= p.p_last AND span.valid_to > p.p_last THEN 1 ELSE 0 END AS span_is_last, CASE WHEN span.valid_from <= p.p_first AND span.valid_to > p.p_first THEN 1 ELSE 0 END AS span_is_first, p.p_days AS span_group_days FROM (SELECT * FROM span_test.fct_inventory_spans span WHERE span.valid_from <= CAST(:range_to AS DATE) AND span.valid_to > CAST(:range_from AS DATE) AND span.valid_from < span.valid_to) span CROSS JOIN LATERAL generate_series(DATE_TRUNC('week', CAST(GREATEST(span.valid_from, CAST(:range_from AS DATE)) AS TIMESTAMP)), DATE_TRUNC('week', CAST(LEAST(span.valid_to - 1, CAST(:range_to AS DATE)) AS TIMESTAMP)), INTERVAL '1 week') AS g(p_start) JOIN span_periods p ON p.p_key = CAST(g.p_start AS DATE) JOIN span_test.mf_time_spine sd ON sd.ds = p.p_first OFFSET 0
                    ) inventory_spans_src_90000
                  ) subq_90007
                ) subq_90008
              ) subq_90009
              WHERE inventory_span__span_is_first = 1
            ) subq_90010
          ) subq_90011
          GROUP BY
            subq_90011.metric_time__week
        ) subq_90012
      ) subq_90017
      ON
        subq_90016.metric_time__week = subq_90017.metric_time__week
      GROUP BY
        COALESCE(subq_90016.metric_time__week, subq_90017.metric_time__week)
    ) subq_90018
  ) subq_90019
  ON
    subq_90015.metric_time__week = subq_90019.metric_time__week
  FULL OUTER JOIN (
    -- Compute Metrics via Expressions
    SELECT
      subq_90024.metric_time__week
      , subq_90024.__received_units AS received_units
    FROM (
      -- Aggregate Inputs for Simple Metrics
      SELECT
        subq_90023.metric_time__week
        , SUM(subq_90023.__received_units) AS __received_units
      FROM (
        -- Select: ['__received_units', 'metric_time__week']
        SELECT
          subq_90022.metric_time__week
          , subq_90022.__received_units
        FROM (
          -- Select: ['__received_units', 'metric_time__week']
          SELECT
            subq_90021.metric_time__week
            , subq_90021.__received_units
          FROM (
            -- Metric Time Dimension 'ds'
            SELECT
              subq_90020.ds__day
              , subq_90020.ds__week
              , subq_90020.ds__month
              , subq_90020.ds__quarter
              , subq_90020.ds__year
              , subq_90020.ds__extract_year
              , subq_90020.ds__extract_quarter
              , subq_90020.ds__extract_month
              , subq_90020.ds__extract_day
              , subq_90020.ds__extract_dow
              , subq_90020.ds__extract_doy
              , subq_90020.receipt__ds__day
              , subq_90020.receipt__ds__week
              , subq_90020.receipt__ds__month
              , subq_90020.receipt__ds__quarter
              , subq_90020.receipt__ds__year
              , subq_90020.receipt__ds__extract_year
              , subq_90020.receipt__ds__extract_quarter
              , subq_90020.receipt__ds__extract_month
              , subq_90020.receipt__ds__extract_day
              , subq_90020.receipt__ds__extract_dow
              , subq_90020.receipt__ds__extract_doy
              , subq_90020.ds__day AS metric_time__day
              , subq_90020.ds__week AS metric_time__week
              , subq_90020.ds__month AS metric_time__month
              , subq_90020.ds__quarter AS metric_time__quarter
              , subq_90020.ds__year AS metric_time__year
              , subq_90020.ds__extract_year AS metric_time__extract_year
              , subq_90020.ds__extract_quarter AS metric_time__extract_quarter
              , subq_90020.ds__extract_month AS metric_time__extract_month
              , subq_90020.ds__extract_day AS metric_time__extract_day
              , subq_90020.ds__extract_dow AS metric_time__extract_dow
              , subq_90020.ds__extract_doy AS metric_time__extract_doy
              , subq_90020.location
              , subq_90020.receipt__location
              , subq_90020.__received_units
            FROM (
              -- Read Elements From Semantic Model 'receipts'
              SELECT
                receipts_src_90000.received_units AS __received_units
                , DATE_TRUNC('day', receipts_src_90000.ds) AS ds__day
                , DATE_TRUNC('week', receipts_src_90000.ds) AS ds__week
                , DATE_TRUNC('month', receipts_src_90000.ds) AS ds__month
                , DATE_TRUNC('quarter', receipts_src_90000.ds) AS ds__quarter
                , DATE_TRUNC('year', receipts_src_90000.ds) AS ds__year
                , EXTRACT(year FROM receipts_src_90000.ds) AS ds__extract_year
                , EXTRACT(quarter FROM receipts_src_90000.ds) AS ds__extract_quarter
                , EXTRACT(month FROM receipts_src_90000.ds) AS ds__extract_month
                , EXTRACT(day FROM receipts_src_90000.ds) AS ds__extract_day
                , EXTRACT(isodow FROM receipts_src_90000.ds) AS ds__extract_dow
                , EXTRACT(doy FROM receipts_src_90000.ds) AS ds__extract_doy
                , DATE_TRUNC('day', receipts_src_90000.ds) AS receipt__ds__day
                , DATE_TRUNC('week', receipts_src_90000.ds) AS receipt__ds__week
                , DATE_TRUNC('month', receipts_src_90000.ds) AS receipt__ds__month
                , DATE_TRUNC('quarter', receipts_src_90000.ds) AS receipt__ds__quarter
                , DATE_TRUNC('year', receipts_src_90000.ds) AS receipt__ds__year
                , EXTRACT(year FROM receipts_src_90000.ds) AS receipt__ds__extract_year
                , EXTRACT(quarter FROM receipts_src_90000.ds) AS receipt__ds__extract_quarter
                , EXTRACT(month FROM receipts_src_90000.ds) AS receipt__ds__extract_month
                , EXTRACT(day FROM receipts_src_90000.ds) AS receipt__ds__extract_day
                , EXTRACT(isodow FROM receipts_src_90000.ds) AS receipt__ds__extract_dow
                , EXTRACT(doy FROM receipts_src_90000.ds) AS receipt__ds__extract_doy
                , receipts_src_90000.location_id AS location
                , receipts_src_90000.location_id AS receipt__location
              FROM span_test.fct_receipts receipts_src_90000
            ) subq_90020
          ) subq_90021
        ) subq_90022
      ) subq_90023
      GROUP BY
        subq_90023.metric_time__week
    ) subq_90024
  ) subq_90025
  ON
    COALESCE(subq_90015.metric_time__week, subq_90019.metric_time__week) = subq_90025.metric_time__week
  GROUP BY
    COALESCE(subq_90015.metric_time__week, subq_90019.metric_time__week, subq_90025.metric_time__week)
) subq_90026
