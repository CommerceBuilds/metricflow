"""FORK: two of the CommerceBuilds fork's claims, checked on the rows a query returns, not on its SQL.

- The derived fill (`CreateSelectColumnForCombineOutputNode`): a derived metric that declares
  `config.meta.fill_nulls_with` fills only in the select that combines metrics' outputs. When its inputs fill too, as
  validation requires, it returns the same value in every group whether it is asked for alone, with its parents, or
  beside another metric; beside another metric it also has the groups only that metric brings in, filled.
- A NULL span end reads as open (`convert_semantic_model.span_periods_sql`): an open span counts the same days as a
  span that ends after the range. PostgreSQL only, as the span read is written for it.
- A span model's last-day and first-day branches at a grain, folded into one read (`FilterMergeOptimizer`), read the
  rows they read unfolded. PostgreSQL only, for the same reason.

The queries run through upstream's harness that executes them: the session's `sql_client` (DuckDB, or PostgreSQL in
the `test-postgres` target) under `MetricFlowEngine.query`, over manifests and tables of the module's own. They need
upstream's fixtures, so a `--noconftest` run skips them.
"""

from __future__ import annotations

import datetime
import logging
import pathlib
from typing import Dict, FrozenSet, Iterator, Optional, Sequence, Tuple

import pytest
from _pytest.fixtures import FixtureRequest
from metricflow_semantics.model.semantic_manifest_lookup import SemanticManifestLookup
from metricflow_semantics.specs.dunder_column_association_resolver import DunderColumnAssociationResolver
from metricflow_semantics.test_helpers.config_helpers import MetricFlowTestConfiguration
from metricflow_semantics.test_helpers.manifest_helpers import mf_load_manifest_from_yaml_directory
from metricflow_semantics.test_helpers.time_helpers import ConfigurableTimeSource

from metricflow.dataflow.optimizer.dataflow_optimizer_factory import DataflowPlanOptimization
from metricflow.dataset import convert_semantic_model
from metricflow.engine.metricflow_engine import MetricFlowEngine, MetricFlowQueryRequest
from metricflow.protocols.sql_client import SqlClient, SqlEngine
from metricflow_semantic_interfaces.test_utils import as_datetime
from tests_metricflow.fixtures.sql_clients.ddl_sql_client import SqlClientWithDDLMethods

logger = logging.getLogger(__name__)

_FILL_MANIFEST_DIRECTORY = pathlib.Path(__file__).parent / "fill_manifest"
_SPAN_MANIFEST_DIRECTORY = pathlib.Path(__file__).parent / "span_manifest"

# A group's key, as text (a week's first day `2020-01-06`, or a location), mapped to a metric's value.
_ValueByGroup = Dict[str, float]


@pytest.fixture
def executing_sql_client(request: FixtureRequest) -> SqlClientWithDDLMethods:
    """Upstream's session SQL client, which can also run DDL. Skips under `--noconftest`, which leaves it out."""
    if request.config.getoption("noconftest"):
        pytest.skip("Executes queries, so it needs upstream's `ddl_sql_client` fixture, left out by `--noconftest`.")
    return request.getfixturevalue("ddl_sql_client")


@pytest.fixture
def schema_name(request: FixtureRequest, executing_sql_client: SqlClientWithDDLMethods) -> Iterator[str]:
    """A schema of the test's own, dropped after it.

    Never the session's schemas: on PostgreSQL the system schema is also upstream's source schema, and a table this
    module creates there (`mf_time_spine`) would replace upstream's own for every later test.
    """
    configuration: MetricFlowTestConfiguration = request.getfixturevalue("mf_test_configuration")
    own_schema_name = f"{configuration.mf_system_schema}_fork_rows"
    executing_sql_client.create_schema(own_schema_name)
    try:
        yield own_schema_name
    finally:
        executing_sql_client.drop_schema(own_schema_name, cascade=True)


def _create_table(sql_client: SqlClient, table: str, columns: str, rows: Sequence[str]) -> None:
    """(Re)creates `table` with `columns` (SQL) and inserts `rows`, each one row's SQL values."""
    sql_client.execute(f"DROP TABLE IF EXISTS {table}")
    sql_client.execute(f"CREATE TABLE {table} ({columns})")
    sql_client.execute(f"INSERT INTO {table} VALUES {', '.join(f'({row})' for row in rows)}")


def _day_rows(first_day: datetime.date, day_count: int, cast_type: str) -> Tuple[str, ...]:
    """One row per day from `first_day`, each the day cast to `cast_type`, e.g. `CAST('2020-01-06' AS TIMESTAMP)`."""
    return tuple(
        f"CAST('{(first_day + datetime.timedelta(days=offset)).isoformat()}' AS {cast_type})"
        for offset in range(day_count)
    )


def _query(
    engine: MetricFlowEngine,
    metric_names: Sequence[str],
    group_by_name: str,
    optimizations: FrozenSet[DataflowPlanOptimization],
    metric_name: str,
) -> _ValueByGroup:
    """Runs the query and returns `metric_name` by group. A NULL value fails the test: the fill exists to prevent it."""
    result = engine.query(
        MetricFlowQueryRequest.create(
            metric_names=metric_names,
            group_by_names=[group_by_name],
            dataflow_plan_optimizations=set(optimizations),
        )
    ).result_df
    assert result is not None
    group_index = result.column_name_index(group_by_name)
    value_index = result.column_name_index(metric_name)
    values: _ValueByGroup = {}
    for row in result.rows:
        value = row[value_index]
        assert value is not None, f"{metric_name} is NULL in group {row[group_index]!r} of {metric_names}"
        # A week is a `datetime`; its day alone names the group.
        values[str(row[group_index])[:10]] = float(str(value))
    return values


@pytest.fixture
def fill_engine(executing_sql_client: SqlClient, schema_name: str) -> MetricFlowEngine:
    """An engine over `fill_manifest/` and its tables.

    The two inputs and the other fact each hold groups the others don't:
      week     2020-01-06  begin 10 + 5, end 7, received 1
      week     2020-01-13  begin 20, end 3
      week     2020-01-20  begin 9 (location d), no end, received 4
      week     2020-01-27  received 2 only
    so by location: a (begin 30, end 7, received 3), b (5, 3), c (received 4 only), d (begin 9 only).
    """
    rows_by_table = {
        "fork_fill_begin_positions": (
            ("a", "2020-01-06", 10),
            ("a", "2020-01-13", 20),
            ("b", "2020-01-06", 5),
            ("d", "2020-01-20", 9),
        ),
        "fork_fill_end_positions": (("a", "2020-01-07", 7), ("b", "2020-01-14", 3)),
        "fork_fill_receipts": (("a", "2020-01-08", 1), ("c", "2020-01-21", 4), ("a", "2020-01-27", 2)),
    }
    for table, rows in rows_by_table.items():
        _create_table(
            executing_sql_client,
            f"{schema_name}.{table}",
            "location_id VARCHAR, ds TIMESTAMP, units INTEGER",
            tuple(f"'{location}', CAST('{day}' AS TIMESTAMP), {units}" for location, day, units in rows),
        )
    _create_table(
        executing_sql_client,
        f"{schema_name}.fork_fill_time_spine",
        "ds TIMESTAMP",
        _day_rows(datetime.date(2020, 1, 1), 60, "TIMESTAMP"),
    )
    manifest = mf_load_manifest_from_yaml_directory(
        _FILL_MANIFEST_DIRECTORY, template_mapping={"source_schema": schema_name}
    )
    return MetricFlowEngine(
        semantic_manifest_lookup=SemanticManifestLookup(manifest),
        sql_client=executing_sql_client,
        column_association_resolver=DunderColumnAssociationResolver(),
        time_source=ConfigurableTimeSource(as_datetime("2020-01-01")),
    )


@pytest.mark.parametrize(
    ("group_by_name", "expected_alone", "only_beside"),
    (
        ("metric_time__week", {"2020-01-06": 22.0, "2020-01-13": 23.0, "2020-01-20": 9.0}, {"2020-01-27": 0.0}),
        ("location", {"a": 37.0, "b": 8.0, "d": 9.0}, {"c": 0.0}),
    ),
    ids=("by_week", "by_location"),
)
@pytest.mark.parametrize(
    "optimizations",
    (DataflowPlanOptimization.enabled_optimizations(), DataflowPlanOptimization.all_optimizations()),
    ids=("enabled_optimizations", "all_optimizations"),
)
def test_a_filled_derived_metric_reads_the_same_rows_three_ways(
    fill_engine: MetricFlowEngine,
    group_by_name: str,
    expected_alone: _ValueByGroup,
    only_beside: _ValueByGroup,
    optimizations: FrozenSet[DataflowPlanOptimization],
) -> None:
    """`total_units` alone, with its parents, and beside `received_units`: equal in every group it has alone.

    Week 2020-01-20 and location d have no `end_units`: alone, `total_units` still reads 9 there, from its inputs'
    own fill. Beside `received_units` it also has that metric's own groups, where the derived fill writes 0; alone,
    those groups have no row at all, which is how MetricFlow treats a filled simple metric too.
    """
    alone = _query(fill_engine, ["total_units"], group_by_name, optimizations, "total_units")
    with_parents = _query(
        fill_engine, ["total_units", "begin_units", "end_units"], group_by_name, optimizations, "total_units"
    )
    beside = _query(fill_engine, ["total_units", "received_units"], group_by_name, optimizations, "total_units")

    assert alone == expected_alone
    assert with_parents == alone
    assert beside == {**alone, **only_beside}


@pytest.fixture
def span_engine(executing_sql_client: SqlClient, schema_name: str) -> Iterator[MetricFlowEngine]:
    """An engine over `span_manifest/`, its range the two weeks from 2026-01-05, and two locations' spans.

    Location `open` holds 2 units from 2026-01-01 with a NULL end; location `closed` holds the same, ending 2027-01-01.
    """
    if executing_sql_client.sql_engine_type is not SqlEngine.POSTGRES:
        pytest.skip("The span read is written for PostgreSQL.")
    _create_table(
        executing_sql_client,
        f"{schema_name}.fct_inventory_spans",
        "location_id VARCHAR, valid_from DATE, valid_to DATE, on_hand_units INTEGER",
        (
            "'open', CAST('2026-01-01' AS DATE), NULL, 2",
            "'closed', CAST('2026-01-01' AS DATE), CAST('2027-01-01' AS DATE), 2",
        ),
    )
    _create_table(
        executing_sql_client,
        f"{schema_name}.fct_receipts",
        "location_id VARCHAR, ds DATE, received_units INTEGER",
        ("'open', CAST('2026-01-06' AS DATE), 1",),
    )
    _create_table(
        executing_sql_client,
        f"{schema_name}.mf_time_spine",
        "ds DATE, fiscal_month VARCHAR",
        tuple(f"{day}, 'FY26-01'" for day in _day_rows(datetime.date(2025, 12, 1), 90, "DATE")),
    )
    saved: Optional[Tuple[str, str]] = convert_semantic_model.SPAN_RANGE_SQL
    convert_semantic_model.SPAN_RANGE_SQL = ("CAST('2026-01-05' AS DATE)", "CAST('2026-01-18' AS DATE)")
    try:
        manifest = mf_load_manifest_from_yaml_directory(
            _SPAN_MANIFEST_DIRECTORY, template_mapping={"source_schema": schema_name}
        )
        yield MetricFlowEngine(
            semantic_manifest_lookup=SemanticManifestLookup(manifest),
            sql_client=executing_sql_client,
            column_association_resolver=DunderColumnAssociationResolver(),
            time_source=ConfigurableTimeSource(as_datetime("2026-01-01")),
        )
    finally:
        convert_semantic_model.SPAN_RANGE_SQL = saved


def test_a_null_span_end_reads_as_open(span_engine: MetricFlowEngine) -> None:
    """An open span counts every day of the range, as a span ending after it does: 2 units over 14 days."""
    optimizations = DataflowPlanOptimization.all_optimizations()
    assert _query(span_engine, ["unit_days"], "location", optimizations, "unit_days") == {"closed": 28.0, "open": 28.0}
    by_week = {"2026-01-05": 4.0, "2026-01-12": 4.0}
    assert _query(span_engine, ["ending_units"], "metric_time__week", optimizations, "ending_units") == by_week


def test_span_branches_merged_at_a_grain_read_the_unmerged_rows(span_engine: MetricFlowEngine) -> None:
    """The last-day and first-day branches by week fold into one read, and read what they read unfolded: 2 units at
    each of two locations on every week's last and first day.
    """
    metric_names = ["ending_units", "beginning_units"]
    merged_optimizations = DataflowPlanOptimization.all_optimizations()
    unmerged_optimizations = frozenset(merged_optimizations - {DataflowPlanOptimization.FILTER_MERGE})
    merged_sql = span_engine.explain(
        MetricFlowQueryRequest.create(
            metric_names=metric_names,
            group_by_names=["metric_time__week"],
            dataflow_plan_optimizations=set(merged_optimizations),
        )
    ).sql_statement.sql
    assert "filters merged" in merged_sql
    by_week = {"2026-01-05": 4.0, "2026-01-12": 4.0}
    for metric_name in metric_names:
        merged = _query(span_engine, metric_names, "metric_time__week", merged_optimizations, metric_name)
        unmerged = _query(span_engine, metric_names, "metric_time__week", unmerged_optimizations, metric_name)
        assert merged == unmerged == by_week
