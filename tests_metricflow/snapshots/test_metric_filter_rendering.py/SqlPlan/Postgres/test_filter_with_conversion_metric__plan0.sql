test_name: test_filter_with_conversion_metric
test_filename: test_metric_filter_rendering.py
sql_engine: Postgres
---
-- Write to DataTable
SELECT
  subq_26.listings
FROM (
  -- Compute Metrics via Expressions
  SELECT
    subq_25.__listings AS listings
  FROM (
    -- Aggregate Inputs for Simple Metrics
    SELECT
      SUM(subq_24.__listings) AS __listings
    FROM (
      -- Select: ['__listings']
      SELECT
        subq_23.__listings
      FROM (
        -- Constrain Output with WHERE
        SELECT
          subq_22.listings AS __listings
          , subq_22.user__visit_buy_conversion_rate
        FROM (
          -- Select: ['__listings', 'user__visit_buy_conversion_rate']
          SELECT
            subq_21.user__visit_buy_conversion_rate
            , subq_21.__listings AS listings
          FROM (
            -- Join Standard Outputs
            SELECT
              subq_20.user__visit_buy_conversion_rate AS user__visit_buy_conversion_rate
              , subq_1.ds__day AS ds__day
              , subq_1.ds__week AS ds__week
              , subq_1.ds__month AS ds__month
              , subq_1.ds__quarter AS ds__quarter
              , subq_1.ds__year AS ds__year
              , subq_1.ds__extract_year AS ds__extract_year
              , subq_1.ds__extract_quarter AS ds__extract_quarter
              , subq_1.ds__extract_month AS ds__extract_month
              , subq_1.ds__extract_day AS ds__extract_day
              , subq_1.ds__extract_dow AS ds__extract_dow
              , subq_1.ds__extract_doy AS ds__extract_doy
              , subq_1.created_at__day AS created_at__day
              , subq_1.created_at__week AS created_at__week
              , subq_1.created_at__month AS created_at__month
              , subq_1.created_at__quarter AS created_at__quarter
              , subq_1.created_at__year AS created_at__year
              , subq_1.created_at__extract_year AS created_at__extract_year
              , subq_1.created_at__extract_quarter AS created_at__extract_quarter
              , subq_1.created_at__extract_month AS created_at__extract_month
              , subq_1.created_at__extract_day AS created_at__extract_day
              , subq_1.created_at__extract_dow AS created_at__extract_dow
              , subq_1.created_at__extract_doy AS created_at__extract_doy
              , subq_1.listing__ds__day AS listing__ds__day
              , subq_1.listing__ds__week AS listing__ds__week
              , subq_1.listing__ds__month AS listing__ds__month
              , subq_1.listing__ds__quarter AS listing__ds__quarter
              , subq_1.listing__ds__year AS listing__ds__year
              , subq_1.listing__ds__extract_year AS listing__ds__extract_year
              , subq_1.listing__ds__extract_quarter AS listing__ds__extract_quarter
              , subq_1.listing__ds__extract_month AS listing__ds__extract_month
              , subq_1.listing__ds__extract_day AS listing__ds__extract_day
              , subq_1.listing__ds__extract_dow AS listing__ds__extract_dow
              , subq_1.listing__ds__extract_doy AS listing__ds__extract_doy
              , subq_1.listing__created_at__day AS listing__created_at__day
              , subq_1.listing__created_at__week AS listing__created_at__week
              , subq_1.listing__created_at__month AS listing__created_at__month
              , subq_1.listing__created_at__quarter AS listing__created_at__quarter
              , subq_1.listing__created_at__year AS listing__created_at__year
              , subq_1.listing__created_at__extract_year AS listing__created_at__extract_year
              , subq_1.listing__created_at__extract_quarter AS listing__created_at__extract_quarter
              , subq_1.listing__created_at__extract_month AS listing__created_at__extract_month
              , subq_1.listing__created_at__extract_day AS listing__created_at__extract_day
              , subq_1.listing__created_at__extract_dow AS listing__created_at__extract_dow
              , subq_1.listing__created_at__extract_doy AS listing__created_at__extract_doy
              , subq_1.metric_time__day AS metric_time__day
              , subq_1.metric_time__week AS metric_time__week
              , subq_1.metric_time__month AS metric_time__month
              , subq_1.metric_time__quarter AS metric_time__quarter
              , subq_1.metric_time__year AS metric_time__year
              , subq_1.metric_time__extract_year AS metric_time__extract_year
              , subq_1.metric_time__extract_quarter AS metric_time__extract_quarter
              , subq_1.metric_time__extract_month AS metric_time__extract_month
              , subq_1.metric_time__extract_day AS metric_time__extract_day
              , subq_1.metric_time__extract_dow AS metric_time__extract_dow
              , subq_1.metric_time__extract_doy AS metric_time__extract_doy
              , subq_1.listing AS listing
              , subq_1.user AS user
              , subq_1.listing__user AS listing__user
              , subq_1.country_latest AS country_latest
              , subq_1.is_lux_latest AS is_lux_latest
              , subq_1.capacity_latest AS capacity_latest
              , subq_1.listing__country_latest AS listing__country_latest
              , subq_1.listing__is_lux_latest AS listing__is_lux_latest
              , subq_1.listing__capacity_latest AS listing__capacity_latest
              , subq_1.__listings AS __listings
              , subq_1.__lux_listings AS __lux_listings
              , subq_1.__smallest_listing AS __smallest_listing
              , subq_1.__largest_listing AS __largest_listing
              , subq_1.__active_listings AS __active_listings
            FROM (
              -- Metric Time Dimension 'ds'
              SELECT
                subq_0.ds__day
                , subq_0.ds__week
                , subq_0.ds__month
                , subq_0.ds__quarter
                , subq_0.ds__year
                , subq_0.ds__extract_year
                , subq_0.ds__extract_quarter
                , subq_0.ds__extract_month
                , subq_0.ds__extract_day
                , subq_0.ds__extract_dow
                , subq_0.ds__extract_doy
                , subq_0.created_at__day
                , subq_0.created_at__week
                , subq_0.created_at__month
                , subq_0.created_at__quarter
                , subq_0.created_at__year
                , subq_0.created_at__extract_year
                , subq_0.created_at__extract_quarter
                , subq_0.created_at__extract_month
                , subq_0.created_at__extract_day
                , subq_0.created_at__extract_dow
                , subq_0.created_at__extract_doy
                , subq_0.listing__ds__day
                , subq_0.listing__ds__week
                , subq_0.listing__ds__month
                , subq_0.listing__ds__quarter
                , subq_0.listing__ds__year
                , subq_0.listing__ds__extract_year
                , subq_0.listing__ds__extract_quarter
                , subq_0.listing__ds__extract_month
                , subq_0.listing__ds__extract_day
                , subq_0.listing__ds__extract_dow
                , subq_0.listing__ds__extract_doy
                , subq_0.listing__created_at__day
                , subq_0.listing__created_at__week
                , subq_0.listing__created_at__month
                , subq_0.listing__created_at__quarter
                , subq_0.listing__created_at__year
                , subq_0.listing__created_at__extract_year
                , subq_0.listing__created_at__extract_quarter
                , subq_0.listing__created_at__extract_month
                , subq_0.listing__created_at__extract_day
                , subq_0.listing__created_at__extract_dow
                , subq_0.listing__created_at__extract_doy
                , subq_0.ds__day AS metric_time__day
                , subq_0.ds__week AS metric_time__week
                , subq_0.ds__month AS metric_time__month
                , subq_0.ds__quarter AS metric_time__quarter
                , subq_0.ds__year AS metric_time__year
                , subq_0.ds__extract_year AS metric_time__extract_year
                , subq_0.ds__extract_quarter AS metric_time__extract_quarter
                , subq_0.ds__extract_month AS metric_time__extract_month
                , subq_0.ds__extract_day AS metric_time__extract_day
                , subq_0.ds__extract_dow AS metric_time__extract_dow
                , subq_0.ds__extract_doy AS metric_time__extract_doy
                , subq_0.listing
                , subq_0.user
                , subq_0.listing__user
                , subq_0.country_latest
                , subq_0.is_lux_latest
                , subq_0.capacity_latest
                , subq_0.listing__country_latest
                , subq_0.listing__is_lux_latest
                , subq_0.listing__capacity_latest
                , subq_0.__listings
                , subq_0.__lux_listings
                , subq_0.__smallest_listing
                , subq_0.__largest_listing
                , subq_0.__active_listings
              FROM (
                -- Read Elements From Semantic Model 'listings_latest'
                SELECT
                  1 AS __listings
                  , 1 AS __lux_listings
                  , listings_latest_src_28000.capacity AS __smallest_listing
                  , listings_latest_src_28000.capacity AS __largest_listing
                  , 1 AS __active_listings
                  , DATE_TRUNC('day', listings_latest_src_28000.created_at) AS ds__day
                  , DATE_TRUNC('week', listings_latest_src_28000.created_at) AS ds__week
                  , DATE_TRUNC('month', listings_latest_src_28000.created_at) AS ds__month
                  , DATE_TRUNC('quarter', listings_latest_src_28000.created_at) AS ds__quarter
                  , DATE_TRUNC('year', listings_latest_src_28000.created_at) AS ds__year
                  , EXTRACT(year FROM listings_latest_src_28000.created_at) AS ds__extract_year
                  , EXTRACT(quarter FROM listings_latest_src_28000.created_at) AS ds__extract_quarter
                  , EXTRACT(month FROM listings_latest_src_28000.created_at) AS ds__extract_month
                  , EXTRACT(day FROM listings_latest_src_28000.created_at) AS ds__extract_day
                  , EXTRACT(isodow FROM listings_latest_src_28000.created_at) AS ds__extract_dow
                  , EXTRACT(doy FROM listings_latest_src_28000.created_at) AS ds__extract_doy
                  , DATE_TRUNC('day', listings_latest_src_28000.created_at) AS created_at__day
                  , DATE_TRUNC('week', listings_latest_src_28000.created_at) AS created_at__week
                  , DATE_TRUNC('month', listings_latest_src_28000.created_at) AS created_at__month
                  , DATE_TRUNC('quarter', listings_latest_src_28000.created_at) AS created_at__quarter
                  , DATE_TRUNC('year', listings_latest_src_28000.created_at) AS created_at__year
                  , EXTRACT(year FROM listings_latest_src_28000.created_at) AS created_at__extract_year
                  , EXTRACT(quarter FROM listings_latest_src_28000.created_at) AS created_at__extract_quarter
                  , EXTRACT(month FROM listings_latest_src_28000.created_at) AS created_at__extract_month
                  , EXTRACT(day FROM listings_latest_src_28000.created_at) AS created_at__extract_day
                  , EXTRACT(isodow FROM listings_latest_src_28000.created_at) AS created_at__extract_dow
                  , EXTRACT(doy FROM listings_latest_src_28000.created_at) AS created_at__extract_doy
                  , listings_latest_src_28000.country AS country_latest
                  , listings_latest_src_28000.is_lux AS is_lux_latest
                  , listings_latest_src_28000.capacity AS capacity_latest
                  , DATE_TRUNC('day', listings_latest_src_28000.created_at) AS listing__ds__day
                  , DATE_TRUNC('week', listings_latest_src_28000.created_at) AS listing__ds__week
                  , DATE_TRUNC('month', listings_latest_src_28000.created_at) AS listing__ds__month
                  , DATE_TRUNC('quarter', listings_latest_src_28000.created_at) AS listing__ds__quarter
                  , DATE_TRUNC('year', listings_latest_src_28000.created_at) AS listing__ds__year
                  , EXTRACT(year FROM listings_latest_src_28000.created_at) AS listing__ds__extract_year
                  , EXTRACT(quarter FROM listings_latest_src_28000.created_at) AS listing__ds__extract_quarter
                  , EXTRACT(month FROM listings_latest_src_28000.created_at) AS listing__ds__extract_month
                  , EXTRACT(day FROM listings_latest_src_28000.created_at) AS listing__ds__extract_day
                  , EXTRACT(isodow FROM listings_latest_src_28000.created_at) AS listing__ds__extract_dow
                  , EXTRACT(doy FROM listings_latest_src_28000.created_at) AS listing__ds__extract_doy
                  , DATE_TRUNC('day', listings_latest_src_28000.created_at) AS listing__created_at__day
                  , DATE_TRUNC('week', listings_latest_src_28000.created_at) AS listing__created_at__week
                  , DATE_TRUNC('month', listings_latest_src_28000.created_at) AS listing__created_at__month
                  , DATE_TRUNC('quarter', listings_latest_src_28000.created_at) AS listing__created_at__quarter
                  , DATE_TRUNC('year', listings_latest_src_28000.created_at) AS listing__created_at__year
                  , EXTRACT(year FROM listings_latest_src_28000.created_at) AS listing__created_at__extract_year
                  , EXTRACT(quarter FROM listings_latest_src_28000.created_at) AS listing__created_at__extract_quarter
                  , EXTRACT(month FROM listings_latest_src_28000.created_at) AS listing__created_at__extract_month
                  , EXTRACT(day FROM listings_latest_src_28000.created_at) AS listing__created_at__extract_day
                  , EXTRACT(isodow FROM listings_latest_src_28000.created_at) AS listing__created_at__extract_dow
                  , EXTRACT(doy FROM listings_latest_src_28000.created_at) AS listing__created_at__extract_doy
                  , listings_latest_src_28000.country AS listing__country_latest
                  , listings_latest_src_28000.is_lux AS listing__is_lux_latest
                  , listings_latest_src_28000.capacity AS listing__capacity_latest
                  , listings_latest_src_28000.listing_id AS listing
                  , listings_latest_src_28000.user_id AS user
                  , listings_latest_src_28000.user_id AS listing__user
                FROM ***************************.dim_listings_latest listings_latest_src_28000
              ) subq_0
            ) subq_1
            LEFT OUTER JOIN (
              -- Select: ['user', 'user__visit_buy_conversion_rate']
              SELECT
                subq_19.user
                , subq_19.user__visit_buy_conversion_rate
              FROM (
                -- Compute Metrics via Expressions
                SELECT
                  subq_18.user
                  , CAST(subq_18.__buys AS DOUBLE PRECISION) / CAST(NULLIF(subq_18.__visits, 0) AS DOUBLE PRECISION) AS user__visit_buy_conversion_rate
                FROM (
                  -- Combine Aggregated Outputs
                  SELECT
                    COALESCE(subq_6.user, subq_17.user) AS user
                    , MAX(subq_6.__visits) AS __visits
                    , MAX(subq_17.__buys) AS __buys
                  FROM (
                    -- Aggregate Inputs for Simple Metrics
                    SELECT
                      subq_5.user
                      , SUM(subq_5.__visits) AS __visits
                    FROM (
                      -- Select: ['__visits', 'user']
                      SELECT
                        subq_4.user
                        , subq_4.__visits
                      FROM (
                        -- Select: ['__visits', 'user']
                        SELECT
                          subq_3.user
                          , subq_3.__visits
                        FROM (
                          -- Metric Time Dimension 'ds'
                          SELECT
                            subq_2.ds__day
                            , subq_2.ds__week
                            , subq_2.ds__month
                            , subq_2.ds__quarter
                            , subq_2.ds__year
                            , subq_2.ds__extract_year
                            , subq_2.ds__extract_quarter
                            , subq_2.ds__extract_month
                            , subq_2.ds__extract_day
                            , subq_2.ds__extract_dow
                            , subq_2.ds__extract_doy
                            , subq_2.visit__ds__day
                            , subq_2.visit__ds__week
                            , subq_2.visit__ds__month
                            , subq_2.visit__ds__quarter
                            , subq_2.visit__ds__year
                            , subq_2.visit__ds__extract_year
                            , subq_2.visit__ds__extract_quarter
                            , subq_2.visit__ds__extract_month
                            , subq_2.visit__ds__extract_day
                            , subq_2.visit__ds__extract_dow
                            , subq_2.visit__ds__extract_doy
                            , subq_2.ds__day AS metric_time__day
                            , subq_2.ds__week AS metric_time__week
                            , subq_2.ds__month AS metric_time__month
                            , subq_2.ds__quarter AS metric_time__quarter
                            , subq_2.ds__year AS metric_time__year
                            , subq_2.ds__extract_year AS metric_time__extract_year
                            , subq_2.ds__extract_quarter AS metric_time__extract_quarter
                            , subq_2.ds__extract_month AS metric_time__extract_month
                            , subq_2.ds__extract_day AS metric_time__extract_day
                            , subq_2.ds__extract_dow AS metric_time__extract_dow
                            , subq_2.ds__extract_doy AS metric_time__extract_doy
                            , subq_2.user
                            , subq_2.session
                            , subq_2.visit__user
                            , subq_2.visit__session
                            , subq_2.referrer_id
                            , subq_2.visit__referrer_id
                            , subq_2.__visits
                            , subq_2.__visits_fill_nulls_with_0_join_to_timespine
                          FROM (
                            -- Read Elements From Semantic Model 'visits_source'
                            SELECT
                              1 AS __visits
                              , 1 AS __visits_fill_nulls_with_0_join_to_timespine
                              , DATE_TRUNC('day', visits_source_src_28000.ds) AS ds__day
                              , DATE_TRUNC('week', visits_source_src_28000.ds) AS ds__week
                              , DATE_TRUNC('month', visits_source_src_28000.ds) AS ds__month
                              , DATE_TRUNC('quarter', visits_source_src_28000.ds) AS ds__quarter
                              , DATE_TRUNC('year', visits_source_src_28000.ds) AS ds__year
                              , EXTRACT(year FROM visits_source_src_28000.ds) AS ds__extract_year
                              , EXTRACT(quarter FROM visits_source_src_28000.ds) AS ds__extract_quarter
                              , EXTRACT(month FROM visits_source_src_28000.ds) AS ds__extract_month
                              , EXTRACT(day FROM visits_source_src_28000.ds) AS ds__extract_day
                              , EXTRACT(isodow FROM visits_source_src_28000.ds) AS ds__extract_dow
                              , EXTRACT(doy FROM visits_source_src_28000.ds) AS ds__extract_doy
                              , visits_source_src_28000.referrer_id
                              , DATE_TRUNC('day', visits_source_src_28000.ds) AS visit__ds__day
                              , DATE_TRUNC('week', visits_source_src_28000.ds) AS visit__ds__week
                              , DATE_TRUNC('month', visits_source_src_28000.ds) AS visit__ds__month
                              , DATE_TRUNC('quarter', visits_source_src_28000.ds) AS visit__ds__quarter
                              , DATE_TRUNC('year', visits_source_src_28000.ds) AS visit__ds__year
                              , EXTRACT(year FROM visits_source_src_28000.ds) AS visit__ds__extract_year
                              , EXTRACT(quarter FROM visits_source_src_28000.ds) AS visit__ds__extract_quarter
                              , EXTRACT(month FROM visits_source_src_28000.ds) AS visit__ds__extract_month
                              , EXTRACT(day FROM visits_source_src_28000.ds) AS visit__ds__extract_day
                              , EXTRACT(isodow FROM visits_source_src_28000.ds) AS visit__ds__extract_dow
                              , EXTRACT(doy FROM visits_source_src_28000.ds) AS visit__ds__extract_doy
                              , visits_source_src_28000.referrer_id AS visit__referrer_id
                              , visits_source_src_28000.user_id AS user
                              , visits_source_src_28000.session_id AS session
                              , visits_source_src_28000.user_id AS visit__user
                              , visits_source_src_28000.session_id AS visit__session
                            FROM ***************************.fct_visits visits_source_src_28000
                          ) subq_2
                        ) subq_3
                      ) subq_4
                    ) subq_5
                    GROUP BY
                      subq_5.user
                  ) subq_6
                  FULL OUTER JOIN (
                    -- Aggregate Inputs for Simple Metrics
                    SELECT
                      subq_16.user
                      , SUM(subq_16.__buys) AS __buys
                    FROM (
                      -- Select: ['__buys', 'user']
                      SELECT
                        subq_15.user
                        , subq_15.__buys
                      FROM (
                        -- Select: ['__buys', 'user']
                        SELECT
                          subq_14.user
                          , subq_14.__buys
                        FROM (
                          -- Find conversions for user within the range of INF
                          SELECT
                            subq_13.metric_time__day
                            , subq_13.user
                            , subq_13.__buys
                            , subq_13.__visits
                          FROM (
                            -- Dedupe the fanout with mf_internal_uuid in the conversion data set
                            SELECT DISTINCT
                              FIRST_VALUE(subq_9.__visits) OVER (
                                PARTITION BY
                                  subq_12.user
                                  , subq_12.metric_time__day
                                  , subq_12.mf_internal_uuid
                                ORDER BY subq_9.metric_time__day DESC
                                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                              ) AS __visits
                              , FIRST_VALUE(subq_9.metric_time__day) OVER (
                                PARTITION BY
                                  subq_12.user
                                  , subq_12.metric_time__day
                                  , subq_12.mf_internal_uuid
                                ORDER BY subq_9.metric_time__day DESC
                                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                              ) AS metric_time__day
                              , FIRST_VALUE(subq_9.user) OVER (
                                PARTITION BY
                                  subq_12.user
                                  , subq_12.metric_time__day
                                  , subq_12.mf_internal_uuid
                                ORDER BY subq_9.metric_time__day DESC
                                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                              ) AS user
                              , subq_12.mf_internal_uuid AS mf_internal_uuid
                              , subq_12.__buys AS __buys
                            FROM (
                              -- Select: ['__visits', 'metric_time__day', 'user']
                              SELECT
                                subq_8.metric_time__day
                                , subq_8.user
                                , subq_8.__visits
                              FROM (
                                -- Select: ['__visits', 'metric_time__day', 'user']
                                SELECT
                                  subq_7.metric_time__day
                                  , subq_7.user
                                  , subq_7.__visits
                                FROM (
                                  -- Metric Time Dimension 'ds'
                                  SELECT
                                    subq_2.ds__day
                                    , subq_2.ds__week
                                    , subq_2.ds__month
                                    , subq_2.ds__quarter
                                    , subq_2.ds__year
                                    , subq_2.ds__extract_year
                                    , subq_2.ds__extract_quarter
                                    , subq_2.ds__extract_month
                                    , subq_2.ds__extract_day
                                    , subq_2.ds__extract_dow
                                    , subq_2.ds__extract_doy
                                    , subq_2.visit__ds__day
                                    , subq_2.visit__ds__week
                                    , subq_2.visit__ds__month
                                    , subq_2.visit__ds__quarter
                                    , subq_2.visit__ds__year
                                    , subq_2.visit__ds__extract_year
                                    , subq_2.visit__ds__extract_quarter
                                    , subq_2.visit__ds__extract_month
                                    , subq_2.visit__ds__extract_day
                                    , subq_2.visit__ds__extract_dow
                                    , subq_2.visit__ds__extract_doy
                                    , subq_2.ds__day AS metric_time__day
                                    , subq_2.ds__week AS metric_time__week
                                    , subq_2.ds__month AS metric_time__month
                                    , subq_2.ds__quarter AS metric_time__quarter
                                    , subq_2.ds__year AS metric_time__year
                                    , subq_2.ds__extract_year AS metric_time__extract_year
                                    , subq_2.ds__extract_quarter AS metric_time__extract_quarter
                                    , subq_2.ds__extract_month AS metric_time__extract_month
                                    , subq_2.ds__extract_day AS metric_time__extract_day
                                    , subq_2.ds__extract_dow AS metric_time__extract_dow
                                    , subq_2.ds__extract_doy AS metric_time__extract_doy
                                    , subq_2.user
                                    , subq_2.session
                                    , subq_2.visit__user
                                    , subq_2.visit__session
                                    , subq_2.referrer_id
                                    , subq_2.visit__referrer_id
                                    , subq_2.__visits
                                    , subq_2.__visits_fill_nulls_with_0_join_to_timespine
                                  FROM (
                                    -- Read Elements From Semantic Model 'visits_source'
                                    SELECT
                                      1 AS __visits
                                      , 1 AS __visits_fill_nulls_with_0_join_to_timespine
                                      , DATE_TRUNC('day', visits_source_src_28000.ds) AS ds__day
                                      , DATE_TRUNC('week', visits_source_src_28000.ds) AS ds__week
                                      , DATE_TRUNC('month', visits_source_src_28000.ds) AS ds__month
                                      , DATE_TRUNC('quarter', visits_source_src_28000.ds) AS ds__quarter
                                      , DATE_TRUNC('year', visits_source_src_28000.ds) AS ds__year
                                      , EXTRACT(year FROM visits_source_src_28000.ds) AS ds__extract_year
                                      , EXTRACT(quarter FROM visits_source_src_28000.ds) AS ds__extract_quarter
                                      , EXTRACT(month FROM visits_source_src_28000.ds) AS ds__extract_month
                                      , EXTRACT(day FROM visits_source_src_28000.ds) AS ds__extract_day
                                      , EXTRACT(isodow FROM visits_source_src_28000.ds) AS ds__extract_dow
                                      , EXTRACT(doy FROM visits_source_src_28000.ds) AS ds__extract_doy
                                      , visits_source_src_28000.referrer_id
                                      , DATE_TRUNC('day', visits_source_src_28000.ds) AS visit__ds__day
                                      , DATE_TRUNC('week', visits_source_src_28000.ds) AS visit__ds__week
                                      , DATE_TRUNC('month', visits_source_src_28000.ds) AS visit__ds__month
                                      , DATE_TRUNC('quarter', visits_source_src_28000.ds) AS visit__ds__quarter
                                      , DATE_TRUNC('year', visits_source_src_28000.ds) AS visit__ds__year
                                      , EXTRACT(year FROM visits_source_src_28000.ds) AS visit__ds__extract_year
                                      , EXTRACT(quarter FROM visits_source_src_28000.ds) AS visit__ds__extract_quarter
                                      , EXTRACT(month FROM visits_source_src_28000.ds) AS visit__ds__extract_month
                                      , EXTRACT(day FROM visits_source_src_28000.ds) AS visit__ds__extract_day
                                      , EXTRACT(isodow FROM visits_source_src_28000.ds) AS visit__ds__extract_dow
                                      , EXTRACT(doy FROM visits_source_src_28000.ds) AS visit__ds__extract_doy
                                      , visits_source_src_28000.referrer_id AS visit__referrer_id
                                      , visits_source_src_28000.user_id AS user
                                      , visits_source_src_28000.session_id AS session
                                      , visits_source_src_28000.user_id AS visit__user
                                      , visits_source_src_28000.session_id AS visit__session
                                    FROM ***************************.fct_visits visits_source_src_28000
                                  ) subq_2
                                ) subq_7
                              ) subq_8
                            ) subq_9
                            INNER JOIN (
                              -- Add column with generated UUID
                              SELECT
                                subq_11.ds__day
                                , subq_11.ds__week
                                , subq_11.ds__month
                                , subq_11.ds__quarter
                                , subq_11.ds__year
                                , subq_11.ds__extract_year
                                , subq_11.ds__extract_quarter
                                , subq_11.ds__extract_month
                                , subq_11.ds__extract_day
                                , subq_11.ds__extract_dow
                                , subq_11.ds__extract_doy
                                , subq_11.ds_month__month
                                , subq_11.ds_month__quarter
                                , subq_11.ds_month__year
                                , subq_11.ds_month__extract_year
                                , subq_11.ds_month__extract_quarter
                                , subq_11.ds_month__extract_month
                                , subq_11.buy__ds__day
                                , subq_11.buy__ds__week
                                , subq_11.buy__ds__month
                                , subq_11.buy__ds__quarter
                                , subq_11.buy__ds__year
                                , subq_11.buy__ds__extract_year
                                , subq_11.buy__ds__extract_quarter
                                , subq_11.buy__ds__extract_month
                                , subq_11.buy__ds__extract_day
                                , subq_11.buy__ds__extract_dow
                                , subq_11.buy__ds__extract_doy
                                , subq_11.buy__ds_month__month
                                , subq_11.buy__ds_month__quarter
                                , subq_11.buy__ds_month__year
                                , subq_11.buy__ds_month__extract_year
                                , subq_11.buy__ds_month__extract_quarter
                                , subq_11.buy__ds_month__extract_month
                                , subq_11.metric_time__day
                                , subq_11.metric_time__week
                                , subq_11.metric_time__month
                                , subq_11.metric_time__quarter
                                , subq_11.metric_time__year
                                , subq_11.metric_time__extract_year
                                , subq_11.metric_time__extract_quarter
                                , subq_11.metric_time__extract_month
                                , subq_11.metric_time__extract_day
                                , subq_11.metric_time__extract_dow
                                , subq_11.metric_time__extract_doy
                                , subq_11.user
                                , subq_11.session_id
                                , subq_11.buy__user
                                , subq_11.buy__session_id
                                , subq_11.__buys_null_filled
                                , subq_11.__buys
                                , subq_11.__buys_fill_nulls_with_0
                                , GEN_RANDOM_UUID() AS mf_internal_uuid
                              FROM (
                                -- Metric Time Dimension 'ds'
                                SELECT
                                  subq_10.ds__day
                                  , subq_10.ds__week
                                  , subq_10.ds__month
                                  , subq_10.ds__quarter
                                  , subq_10.ds__year
                                  , subq_10.ds__extract_year
                                  , subq_10.ds__extract_quarter
                                  , subq_10.ds__extract_month
                                  , subq_10.ds__extract_day
                                  , subq_10.ds__extract_dow
                                  , subq_10.ds__extract_doy
                                  , subq_10.ds_month__month
                                  , subq_10.ds_month__quarter
                                  , subq_10.ds_month__year
                                  , subq_10.ds_month__extract_year
                                  , subq_10.ds_month__extract_quarter
                                  , subq_10.ds_month__extract_month
                                  , subq_10.buy__ds__day
                                  , subq_10.buy__ds__week
                                  , subq_10.buy__ds__month
                                  , subq_10.buy__ds__quarter
                                  , subq_10.buy__ds__year
                                  , subq_10.buy__ds__extract_year
                                  , subq_10.buy__ds__extract_quarter
                                  , subq_10.buy__ds__extract_month
                                  , subq_10.buy__ds__extract_day
                                  , subq_10.buy__ds__extract_dow
                                  , subq_10.buy__ds__extract_doy
                                  , subq_10.buy__ds_month__month
                                  , subq_10.buy__ds_month__quarter
                                  , subq_10.buy__ds_month__year
                                  , subq_10.buy__ds_month__extract_year
                                  , subq_10.buy__ds_month__extract_quarter
                                  , subq_10.buy__ds_month__extract_month
                                  , subq_10.ds__day AS metric_time__day
                                  , subq_10.ds__week AS metric_time__week
                                  , subq_10.ds__month AS metric_time__month
                                  , subq_10.ds__quarter AS metric_time__quarter
                                  , subq_10.ds__year AS metric_time__year
                                  , subq_10.ds__extract_year AS metric_time__extract_year
                                  , subq_10.ds__extract_quarter AS metric_time__extract_quarter
                                  , subq_10.ds__extract_month AS metric_time__extract_month
                                  , subq_10.ds__extract_day AS metric_time__extract_day
                                  , subq_10.ds__extract_dow AS metric_time__extract_dow
                                  , subq_10.ds__extract_doy AS metric_time__extract_doy
                                  , subq_10.user
                                  , subq_10.session_id
                                  , subq_10.buy__user
                                  , subq_10.buy__session_id
                                  , subq_10.__buys_null_filled
                                  , subq_10.__buys
                                  , subq_10.__buys_fill_nulls_with_0
                                FROM (
                                  -- Read Elements From Semantic Model 'buys_source'
                                  SELECT
                                    1 AS __buys_null_filled
                                    , 1 AS __buys
                                    , 1 AS __buys_fill_nulls_with_0
                                    , 1 AS __buys_month
                                    , DATE_TRUNC('day', buys_source_src_28000.ds) AS ds__day
                                    , DATE_TRUNC('week', buys_source_src_28000.ds) AS ds__week
                                    , DATE_TRUNC('month', buys_source_src_28000.ds) AS ds__month
                                    , DATE_TRUNC('quarter', buys_source_src_28000.ds) AS ds__quarter
                                    , DATE_TRUNC('year', buys_source_src_28000.ds) AS ds__year
                                    , EXTRACT(year FROM buys_source_src_28000.ds) AS ds__extract_year
                                    , EXTRACT(quarter FROM buys_source_src_28000.ds) AS ds__extract_quarter
                                    , EXTRACT(month FROM buys_source_src_28000.ds) AS ds__extract_month
                                    , EXTRACT(day FROM buys_source_src_28000.ds) AS ds__extract_day
                                    , EXTRACT(isodow FROM buys_source_src_28000.ds) AS ds__extract_dow
                                    , EXTRACT(doy FROM buys_source_src_28000.ds) AS ds__extract_doy
                                    , DATE_TRUNC('month', buys_source_src_28000.ds_month) AS ds_month__month
                                    , DATE_TRUNC('quarter', buys_source_src_28000.ds_month) AS ds_month__quarter
                                    , DATE_TRUNC('year', buys_source_src_28000.ds_month) AS ds_month__year
                                    , EXTRACT(year FROM buys_source_src_28000.ds_month) AS ds_month__extract_year
                                    , EXTRACT(quarter FROM buys_source_src_28000.ds_month) AS ds_month__extract_quarter
                                    , EXTRACT(month FROM buys_source_src_28000.ds_month) AS ds_month__extract_month
                                    , DATE_TRUNC('day', buys_source_src_28000.ds) AS buy__ds__day
                                    , DATE_TRUNC('week', buys_source_src_28000.ds) AS buy__ds__week
                                    , DATE_TRUNC('month', buys_source_src_28000.ds) AS buy__ds__month
                                    , DATE_TRUNC('quarter', buys_source_src_28000.ds) AS buy__ds__quarter
                                    , DATE_TRUNC('year', buys_source_src_28000.ds) AS buy__ds__year
                                    , EXTRACT(year FROM buys_source_src_28000.ds) AS buy__ds__extract_year
                                    , EXTRACT(quarter FROM buys_source_src_28000.ds) AS buy__ds__extract_quarter
                                    , EXTRACT(month FROM buys_source_src_28000.ds) AS buy__ds__extract_month
                                    , EXTRACT(day FROM buys_source_src_28000.ds) AS buy__ds__extract_day
                                    , EXTRACT(isodow FROM buys_source_src_28000.ds) AS buy__ds__extract_dow
                                    , EXTRACT(doy FROM buys_source_src_28000.ds) AS buy__ds__extract_doy
                                    , DATE_TRUNC('month', buys_source_src_28000.ds_month) AS buy__ds_month__month
                                    , DATE_TRUNC('quarter', buys_source_src_28000.ds_month) AS buy__ds_month__quarter
                                    , DATE_TRUNC('year', buys_source_src_28000.ds_month) AS buy__ds_month__year
                                    , EXTRACT(year FROM buys_source_src_28000.ds_month) AS buy__ds_month__extract_year
                                    , EXTRACT(quarter FROM buys_source_src_28000.ds_month) AS buy__ds_month__extract_quarter
                                    , EXTRACT(month FROM buys_source_src_28000.ds_month) AS buy__ds_month__extract_month
                                    , buys_source_src_28000.user_id AS user
                                    , buys_source_src_28000.session_id
                                    , buys_source_src_28000.user_id AS buy__user
                                    , buys_source_src_28000.session_id AS buy__session_id
                                  FROM ***************************.fct_buys buys_source_src_28000
                                ) subq_10
                              ) subq_11
                            ) subq_12
                            ON
                              (
                                subq_9.user = subq_12.user
                              ) AND (
                                (subq_9.metric_time__day <= subq_12.metric_time__day)
                              )
                          ) subq_13
                        ) subq_14
                      ) subq_15
                    ) subq_16
                    GROUP BY
                      subq_16.user
                  ) subq_17
                  ON
                    subq_6.user = subq_17.user
                  GROUP BY
                    COALESCE(subq_6.user, subq_17.user)
                ) subq_18
              ) subq_19
            ) subq_20
            ON
              subq_1.user = subq_20.user
          ) subq_21
        ) subq_22
        WHERE user__visit_buy_conversion_rate > 2
      ) subq_23
    ) subq_24
  ) subq_25
) subq_26
