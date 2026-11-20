"""FORK: the span read and the derived-metric fill, rendered as Postgres SQL and compared with snapshot files.

These cover the CommerceBuilds fork's four engine changes:
- a validity-window model may hold measures and needs no natural entity (the manifest below validates);
- such a model is read once per period of the requested grain inside the range (`span_periods_sql`), by equality
  joins only and fenced with `OFFSET 0`;
- one read per semantic model and grain in a plan (`DataflowPlanBuilder._span_read_at_grain`);
- a derived metric's `config.meta.fill_nulls_with` fills in the select that combines metrics' outputs.

The module builds its own manifest and renders with the Postgres renderer directly, so it needs no database and
runs the same under every SQL engine the suite is run with. Snapshots follow upstream's layout and are written with
`--overwrite-snapshots`, as upstream's are.
"""

from __future__ import annotations

import pathlib
from typing import Iterator, Optional, Sequence

import pytest
from _pytest.fixtures import FixtureRequest
from metricflow_semantics.dag.mf_dag import DagId
from metricflow_semantics.model.semantic_manifest_lookup import SemanticManifestLookup
from metricflow_semantics.query.query_parser import MetricFlowQueryParser
from metricflow_semantics.specs.dunder_column_association_resolver import DunderColumnAssociationResolver
from metricflow_semantics.test_helpers.manifest_helpers import mf_load_manifest_from_yaml_directory
from metricflow_semantics.test_helpers.snapshot_helpers import (
    OVERWRITE_SNAPSHOTS_CLI_FLAG,
    SnapshotConfiguration,
    assert_snapshot_text_equal,
)
from metricflow_semantics.dag.sequential_id import SequentialIdGenerator

from metricflow.dataflow.builder.dataflow_plan_builder import DataflowPlanBuilder
from metricflow.dataflow.builder.source_node import SourceNodeBuilder
from metricflow.dataflow.optimizer.dataflow_optimizer_factory import DataflowPlanOptimization
from metricflow.dataset import convert_semantic_model
from metricflow.dataset.convert_semantic_model import SemanticModelToDataSetConverter
from metricflow.plan_conversion.to_sql_plan.dataflow_to_subquery import DataflowNodeToSqlSubqueryVisitor
from metricflow.plan_conversion.to_sql_plan.dataflow_to_sql import DataflowToSqlPlanConverter
from metricflow.protocols.sql_client import SqlEngine
from metricflow.sql.optimizer.optimization_levels import SqlOptimizationLevel
from metricflow.sql.render.postgres import PostgresSQLSqlPlanRenderer

_TESTS_DIRECTORY = pathlib.Path(__file__).parent.parent
_SPAN_MANIFEST_DIRECTORY = pathlib.Path(__file__).parent / "span_manifest"
_SOURCE_SCHEMA = "span_test"
# The range every span read is clipped to: two SQL date expressions an embedding service binds.
_SPAN_RANGE_SQL = ("CAST(:range_from AS DATE)", "CAST(:range_to AS DATE)")
# IDs start here in every fixture and test, whatever the session's own fixtures did before.
_ID_START = 90000


class _SpanEngine:
    """The objects a test needs to build and render a plan over the span manifest."""

    def __init__(self) -> None:
        manifest = mf_load_manifest_from_yaml_directory(
            _SPAN_MANIFEST_DIRECTORY, template_mapping={"source_schema": _SOURCE_SCHEMA}
        )
        self.lookup = SemanticManifestLookup(manifest)
        self.resolver = DunderColumnAssociationResolver()
        converter = SemanticModelToDataSetConverter(column_association_resolver=self.resolver, manifest_lookup=self.lookup)
        data_sets = [
            converter.create_sql_source_data_set(reference)
            for reference in sorted(
                self.lookup.semantic_model_lookup.model_reference_to_model, key=lambda r: r.semantic_model_name
            )
        ]
        self.source_node_builder = SourceNodeBuilder(self.resolver, self.lookup)
        self.source_node_set = self.source_node_builder.create_from_data_sets(data_sets)
        self.node_output_resolver = DataflowNodeToSqlSubqueryVisitor(
            column_association_resolver=self.resolver, semantic_manifest_lookup=self.lookup
        )
        self.node_output_resolver.cache_output_data_sets(self.source_node_set.all_nodes)
        self.query_parser = MetricFlowQueryParser(semantic_manifest_lookup=self.lookup)
        self.to_sql = DataflowToSqlPlanConverter(column_association_resolver=self.resolver, semantic_manifest_lookup=self.lookup)

    def plan_builder(self) -> DataflowPlanBuilder:
        """A new builder per test: it holds a stateful cache."""
        return DataflowPlanBuilder(
            source_node_set=self.source_node_set,
            semantic_manifest_lookup=self.lookup,
            node_output_resolver=self.node_output_resolver.copy(),
            column_association_resolver=self.resolver,
            source_node_builder=self.source_node_builder,
        )


@pytest.fixture(scope="module")
def span_engine() -> Iterator[_SpanEngine]:
    """The span manifest's engine objects, built with the range set, which a span read needs."""
    saved = convert_semantic_model.SPAN_RANGE_SQL
    convert_semantic_model.SPAN_RANGE_SQL = _SPAN_RANGE_SQL
    try:
        with SequentialIdGenerator.id_number_space(_ID_START):
            yield _SpanEngine()
    finally:
        convert_semantic_model.SPAN_RANGE_SQL = saved


@pytest.fixture
def span_snapshot_configuration(request: FixtureRequest) -> SnapshotConfiguration:
    """Upstream's snapshot layout: `tests_metricflow/snapshots/<test file>/SqlPlan/Postgres/<test>__<plan>.sql`."""
    return SnapshotConfiguration(
        display_snapshots=False,
        overwrite_snapshots=bool(request.config.getoption(OVERWRITE_SNAPSHOTS_CLI_FLAG, default=False)),
        snapshot_directory=_TESTS_DIRECTORY / "snapshots",
        tests_directory=_TESTS_DIRECTORY,
    )


def _render(
    request: FixtureRequest,
    span_engine: _SpanEngine,
    snapshot_configuration: SnapshotConfiguration,
    metric_names: Sequence[str],
    group_by_names: Sequence[str],
    expectation_description: Optional[str] = None,
) -> str:
    """Render the query without and with optimizations, as `render_and_check` does, and check both snapshots.

    Returns the optimized SQL, so a test can also assert on its shape.
    """
    saved = convert_semantic_model.SPAN_RANGE_SQL
    convert_semantic_model.SPAN_RANGE_SQL = _SPAN_RANGE_SQL
    try:
        with SequentialIdGenerator.id_number_space(_ID_START):
            query_spec = span_engine.query_parser.parse_and_validate_query(
                metric_names=metric_names, group_by_names=group_by_names
            ).query_spec
            renderer = PostgresSQLSqlPlanRenderer()
            sql = ""
            for plan_id, optimizations, level in (
                ("plan0", (), SqlOptimizationLevel.O0),
                (
                    "plan0_optimized",
                    DataflowPlanOptimization.enabled_optimizations(),
                    SqlOptimizationLevel.default_level(),
                ),
            ):
                plan = span_engine.plan_builder().build_plan(query_spec, optimizations=optimizations)
                sql_plan = span_engine.to_sql.convert_to_sql_plan(
                    sql_engine_type=SqlEngine.POSTGRES,
                    dataflow_plan_node=plan.sink_node,
                    optimization_level=level,
                    sql_query_plan_id=DagId.from_str(plan_id),
                ).sql_plan
                sql = renderer.render_sql_plan(sql_plan).sql
                assert_snapshot_text_equal(
                    request=request,
                    snapshot_configuration=snapshot_configuration,
                    group_id=sql_plan.__class__.__name__,
                    snapshot_id=sql_plan.dag_id.id_str,
                    snapshot_text=sql,
                    snapshot_file_extension=".sql",
                    additional_sub_directories_for_snapshots=(SqlEngine.POSTGRES.value,),
                    additional_header_fields={"sql_engine": SqlEngine.POSTGRES.value},
                    expectation_description=expectation_description,
                )
            return sql
    finally:
        convert_semantic_model.SPAN_RANGE_SQL = saved


def test_span_read_at_a_standard_grain(
    request: FixtureRequest, span_engine: _SpanEngine, span_snapshot_configuration: SnapshotConfiguration
) -> None:
    """A span model by week: each span expanded straight to its weeks' first days, joined on that day."""
    sql = _render(request, span_engine, span_snapshot_configuration, ["unit_days"], ["metric_time__week"])
    assert "generate_series(DATE_TRUNC('week'" in sql
    assert "CAST(:range_from AS DATE)" in sql and "CAST(:range_to AS DATE)" in sql


def test_span_read_at_a_fiscal_grain(
    request: FixtureRequest, span_engine: _SpanEngine, span_snapshot_configuration: SnapshotConfiguration
) -> None:
    """A span model by a custom grain: the range's periods numbered from the spine, each span expanded by number."""
    sql = _render(request, span_engine, span_snapshot_configuration, ["unit_days"], ["metric_time__fiscal_month"])
    assert "ROW_NUMBER() OVER (ORDER BY MIN(d.ds))" in sql
    assert "generate_series(lo.p_no, hi.p_no)" in sql


def test_span_read_with_no_grain(
    request: FixtureRequest, span_engine: _SpanEngine, span_snapshot_configuration: SnapshotConfiguration
) -> None:
    """A span model with no time grain: the whole range as one period."""
    sql = _render(request, span_engine, span_snapshot_configuration, ["unit_days"], ["location"])
    assert "generate_series" not in sql
    assert "CAST(:range_from AS DATE)" in sql and "CAST(:range_to AS DATE)" in sql


def test_last_day_flag(
    request: FixtureRequest, span_engine: _SpanEngine, span_snapshot_configuration: SnapshotConfiguration
) -> None:
    """A balance on each week's last day: the metric's filter on `span_is_last`."""
    sql = _render(request, span_engine, span_snapshot_configuration, ["ending_units"], ["metric_time__week"])
    assert "span_is_last" in sql


def test_first_day_flag(
    request: FixtureRequest, span_engine: _SpanEngine, span_snapshot_configuration: SnapshotConfiguration
) -> None:
    """A balance on each week's first day: the metric's filter on `span_is_first`."""
    sql = _render(request, span_engine, span_snapshot_configuration, ["beginning_units"], ["metric_time__week"])
    assert "span_is_first" in sql


def test_fence_keeps_outer_filters_out_of_the_read(
    request: FixtureRequest, span_engine: _SpanEngine, span_snapshot_configuration: SnapshotConfiguration
) -> None:
    """The read ends in `OFFSET 0`, and a flag filter stays outside it.

    Both flags are read in one plan, so the read is shared and each branch filters it from outside.
    """
    sql = _render(
        request,
        span_engine,
        span_snapshot_configuration,
        ["ending_units", "beginning_units"],
        ["metric_time__fiscal_month"],
    )
    assert sql.count("WITH span_periods") == 1, "both branches share one read"
    fence = sql.index(" OFFSET 0")
    fenced_read = sql[sql.index("WITH span_periods") : fence]
    outside = sql[fence:]
    for flag in ("span_is_last", "span_is_first"):
        assert f"{flag} = 1" not in fenced_read
        assert f"WHERE inventory_span__{flag} = 1" in outside


def test_derived_metric_fill(
    request: FixtureRequest, span_engine: _SpanEngine, span_snapshot_configuration: SnapshotConfiguration
) -> None:
    """A derived metric with `config.meta.fill_nulls_with` fills in the select that combines metrics' outputs."""
    sql = _render(
        request,
        span_engine,
        span_snapshot_configuration,
        ["unit_change", "unit_change_unfilled", "received_units"],
        ["metric_time__week"],
    )
    assert "COALESCE(MAX(subq_" in sql and ".unit_change), 0) AS unit_change" in sql
    assert "MAX(subq_" in sql and ".unit_change_unfilled) AS unit_change_unfilled" in sql
