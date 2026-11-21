test_name: test_query_with_derived_metric_in_where_filter
test_filename: test_metric_filter_rendering.py
docstring:
  Tests a query with a derived metric in the query-level where filter.
sql_engine: DuckDB
---
-- Constrain Output with WHERE
-- Select: ['__listings']
-- Aggregate Inputs for Simple Metrics
-- Compute Metrics via Expressions
-- Write to DataTable
SELECT
  SUM(listings) AS listings
FROM (
  -- Join Standard Outputs
  -- Select: ['__listings', 'listing__views_times_booking_value']
  SELECT
    subq_39.listing__views_times_booking_value AS listing__views_times_booking_value
    , subq_24.__listings AS listings
  FROM (
    -- Read Elements From Semantic Model 'listings_latest'
    -- Metric Time Dimension 'ds'
    SELECT
      listing_id AS listing
      , 1 AS __listings
    FROM ***************************.dim_listings_latest listings_latest_src_28000
  ) subq_24
  LEFT OUTER JOIN (
    -- Compute Metrics via Expressions
    -- Select: ['listing', 'listing__views_times_booking_value']
    SELECT
      listing
      , booking_value * views AS listing__views_times_booking_value
    FROM (
      -- Combine Aggregated Outputs
      SELECT
        COALESCE(subq_30.listing, subq_36.listing) AS listing
        , MAX(subq_30.booking_value) AS booking_value
        , MAX(subq_36.views) AS views
      FROM (
        -- Read Elements From Semantic Model 'bookings_source'
        -- Metric Time Dimension 'ds'
        -- Select: ['__booking_value', 'listing']
        -- Select: ['__booking_value', 'listing']
        -- Aggregate Inputs for Simple Metrics
        -- Compute Metrics via Expressions
        SELECT
          listing_id AS listing
          , SUM(booking_value) AS booking_value
        FROM ***************************.fct_bookings bookings_source_src_28000
        GROUP BY
          listing_id
      ) subq_30
      FULL OUTER JOIN (
        -- Aggregate Inputs for Simple Metrics
        -- Compute Metrics via Expressions
        SELECT
          listing
          , SUM(__views) AS views
        FROM (
          -- Read Elements From Semantic Model 'views_source'
          -- Metric Time Dimension 'ds'
          -- Select: ['__views', 'listing']
          -- Select: ['__views', 'listing']
          SELECT
            listing_id AS listing
            , 1 AS __views
          FROM ***************************.fct_views views_source_src_28000
        ) subq_34
        GROUP BY
          listing
      ) subq_36
      ON
        subq_30.listing = subq_36.listing
      GROUP BY
        COALESCE(subq_30.listing, subq_36.listing)
    ) subq_37
  ) subq_39
  ON
    subq_24.listing = subq_39.listing
) subq_41
WHERE listing__views_times_booking_value > 1
