"""FORK: the span read and the derived-metric fill, rendered as Postgres SQL and compared with snapshot files.

These cover four of the CommerceBuilds fork's engine changes (the rest: `test_recipe_search_ids.py`,
`test_postgres_spellings.py`, `test_passthrough.py`), each rendered with no optimization, with upstream's enabled
ones, and with every one, as the embedding service renders:
- a validity-window model may hold measures and needs no natural entity (the manifest below validates);
- such a model is read once per period of the requested grain inside the range (`span_periods_sql`), by equality
  joins only and fenced with `OFFSET 0`;
- one read per semantic model and grain in a plan (`DataflowPlanBuilder._span_read_at_grain`), refusing with
  `SpanReadError` what it can't answer exactly: a time constraint, an offset, a cumulative window, a date part, a
  filter on the span's time other than the bound range;
- a NULL span end reads as open;
- a derived metric's `config.meta.fill_nulls_with` fills in the select that combines metrics' outputs.

The module builds its own manifest and renders with the Postgres renderer directly, so it needs no database and
runs the same under every SQL engine the suite is run with. Snapshots follow upstream's layout and are written with
`--overwrite-snapshots`, as upstream's are.
"""

from __future__ import annotations

import datetime
import pathlib
import textwrap
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Tuple

import pytest
from _pytest.fixtures import FixtureRequest
from metricflow_semantics.dag.mf_dag import DagId
from metricflow_semantics.dag.sequential_id import SequentialIdGenerator
from metricflow_semantics.errors.error_classes import SemanticManifestConfigurationError
from metricflow_semantics.model.semantic_manifest_lookup import SemanticManifestLookup
from metricflow_semantics.protocols.query_parameter import GroupByQueryParameter
from metricflow_semantics.query.query_parser import MetricFlowQueryParser
from metricflow_semantics.specs.dunder_column_association_resolver import DunderColumnAssociationResolver
from metricflow_semantics.specs.query_param_implementations import TimeDimensionParameter
from metricflow_semantics.test_helpers.manifest_helpers import mf_load_manifest_from_yaml_directory
from metricflow_semantics.test_helpers.snapshot_helpers import (
    OVERWRITE_SNAPSHOTS_CLI_FLAG,
    SnapshotConfiguration,
    assert_snapshot_text_equal,
)

from metricflow.dataflow.builder.dataflow_plan_builder import DataflowPlanBuilder
from metricflow.dataflow.builder.source_node import SourceNodeBuilder
from metricflow.dataflow.optimizer.dataflow_optimizer_factory import DataflowPlanOptimization
from metricflow.dataset import convert_semantic_model
from metricflow.dataset.convert_semantic_model import SemanticModelToDataSetConverter, SpanReadError
from metricflow.plan_conversion.to_sql_plan.dataflow_to_sql import DataflowToSqlPlanConverter, SqlGenerationError
from metricflow.plan_conversion.to_sql_plan.dataflow_to_subquery import DataflowNodeToSqlSubqueryVisitor
from metricflow.protocols.sql_client import SqlEngine
from metricflow.sql.optimizer.optimization_levels import SqlOptimizationLevel
from metricflow.sql.render.postgres import PostgresSQLSqlPlanRenderer
from metricflow_semantic_interfaces.implementations.semantic_manifest import PydanticSemanticManifest
from metricflow_semantic_interfaces.parsing.dir_to_model import parse_yaml_files_to_validation_ready_semantic_manifest
from metricflow_semantic_interfaces.parsing.objects import YamlConfigFile
from metricflow_semantic_interfaces.type_enums.date_part import DatePart

_TESTS_DIRECTORY = pathlib.Path(__file__).parent.parent
_SPAN_MANIFEST_DIRECTORY = pathlib.Path(__file__).parent / "span_manifest"
_SOURCE_SCHEMA = "span_test"
# The range every span read is clipped to: two SQL date expressions an embedding service binds.
_SPAN_RANGE_SQL = ("CAST(:range_from AS DATE)", "CAST(:range_to AS DATE)")
# IDs start here in every fixture and test, whatever the session's own fixtures did before.
_ID_START = 90000


class _SpanEngine:
    """The objects a test needs to build and render a plan over the span manifest."""

    def __init__(self, manifest: Optional[PydanticSemanticManifest] = None) -> None:
        if manifest is None:
            manifest = mf_load_manifest_from_yaml_directory(
                _SPAN_MANIFEST_DIRECTORY, template_mapping={"source_schema": _SOURCE_SCHEMA}
            )
        self.lookup = SemanticManifestLookup(manifest)
        self.resolver = DunderColumnAssociationResolver()
        converter = SemanticModelToDataSetConverter(
            column_association_resolver=self.resolver, manifest_lookup=self.lookup
        )
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
        self.to_sql = DataflowToSqlPlanConverter(
            column_association_resolver=self.resolver, semantic_manifest_lookup=self.lookup
        )

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
    """Render the query with no optimization, upstream's enabled ones and every one, and check each snapshot.

    Returns the SQL rendered with every optimization, so a test can also assert on its shape.
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
                # Every optimization on, passthrough metric evaluation included, as the embedding service renders.
                (
                    "plan0_all_optimizations",
                    DataflowPlanOptimization.all_optimizations(),
                    SqlOptimizationLevel.default_level(),
                ),
            ):
                plan = span_engine.plan_builder().build_plan(query_spec, optimizations=frozenset(optimizations))
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
        # With every optimization on, both flags filter one filter-merged read (`FilterMergeOptimizer`), whose WHERE
        # is the OR of the two, so each flag is in that WHERE, outside the fence, not in a WHERE of its own.
        assert f"inventory_span__{flag} = 1" in outside


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


def _build_sql(
    span_engine: _SpanEngine,
    metric_names: Sequence[str],
    group_by_names: Sequence[str] = (),
    group_by: Optional[Tuple[GroupByQueryParameter, ...]] = None,
    where_constraint_strs: Sequence[str] = (),
    time_constraint: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
) -> str:
    """Build and render one query with every optimization on, with no snapshot. A refusal raises from the builder."""
    saved = convert_semantic_model.SPAN_RANGE_SQL
    convert_semantic_model.SPAN_RANGE_SQL = _SPAN_RANGE_SQL
    try:
        with SequentialIdGenerator.id_number_space(_ID_START):
            query_spec = span_engine.query_parser.parse_and_validate_query(
                metric_names=metric_names,
                group_by_names=group_by_names or None,
                group_by=group_by,
                where_constraint_strs=where_constraint_strs or None,
                time_constraint_start=time_constraint[0] if time_constraint else None,
                time_constraint_end=time_constraint[1] if time_constraint else None,
            ).query_spec
            plan = span_engine.plan_builder().build_plan(
                query_spec, optimizations=DataflowPlanOptimization.all_optimizations()
            )
            sql_plan = span_engine.to_sql.convert_to_sql_plan(
                sql_engine_type=SqlEngine.POSTGRES,
                dataflow_plan_node=plan.sink_node,
                optimization_level=SqlOptimizationLevel.default_level(),
                sql_query_plan_id=DagId.from_str("plan0"),
            ).sql_plan
            return PostgresSQLSqlPlanRenderer().render_sql_plan(sql_plan).sql
    finally:
        convert_semantic_model.SPAN_RANGE_SQL = saved


def _span_engine_with(file_edits: Dict[str, Callable[[str], str]]) -> _SpanEngine:
    """An engine over the span manifest with some of its files' text edited, transformed but not validated.

    `file_edits` maps a file's name in `span_manifest/` to a function of its text.
    """
    files = []
    for path in sorted(_SPAN_MANIFEST_DIRECTORY.glob("*.yaml")):
        contents = path.read_text().replace("$source_schema", _SOURCE_SCHEMA)
        edit_text = file_edits.get(path.name)
        files.append(YamlConfigFile(filepath=str(path), contents=edit_text(contents) if edit_text else contents))
    manifest = parse_yaml_files_to_validation_ready_semantic_manifest(files).semantic_manifest
    saved = convert_semantic_model.SPAN_RANGE_SQL
    convert_semantic_model.SPAN_RANGE_SQL = _SPAN_RANGE_SQL
    try:
        with SequentialIdGenerator.id_number_space(_ID_START):
            return _SpanEngine(manifest)
    finally:
        convert_semantic_model.SPAN_RANGE_SQL = saved


def _replaced(old: str, new: str) -> Callable[[str], str]:
    """A file edit that replaces `old`, which must occur exactly once, with `new`."""

    def edit_text(contents: str) -> str:
        assert contents.count(old) == 1, old
        return contents.replace(old, new)

    return edit_text


# Any time constraint on a request.
_TIME_CONSTRAINT = (datetime.datetime(2026, 1, 5), datetime.datetime(2026, 2, 1))


@pytest.mark.parametrize("group_by_names", (["metric_time__week"], ["location"]), ids=("by_week", "no_grain"))
def test_a_time_constraint_is_refused(span_engine: _SpanEngine, group_by_names: Sequence[str]) -> None:
    """A time constraint keeps or drops whole periods by their first day, grouped by a grain or not: refused."""
    with pytest.raises(SpanReadError, match="'unit_days' can't be read under a time constraint"):
        _build_sql(span_engine, ["unit_days"], group_by_names, time_constraint=_TIME_CONSTRAINT)


def test_an_offset_is_refused(span_engine: _SpanEngine) -> None:
    """An offset reads periods outside the bound range, which the span read never makes: refused."""
    with pytest.raises(SpanReadError, match="'unit_days' can't be read at an offset"):
        _build_sql(span_engine, ["unit_days_a_month_before"], ["metric_time__month"])


def test_a_cumulative_window_is_refused(span_engine: _SpanEngine) -> None:
    """A cumulative window reads periods outside the bound range, over rows dated by their period's first day."""
    with pytest.raises(SpanReadError, match="'unit_days' can't be read in a cumulative window"):
        _build_sql(span_engine, ["unit_days_to_date"], ["metric_time__month"])


def test_two_grains_are_refused(span_engine: _SpanEngine) -> None:
    """A span read is made at one grain, so a request grouped by two is refused with the typed error."""
    with pytest.raises(SpanReadError, match="'unit_days' is read at one time grain"):
        _build_sql(span_engine, ["unit_days"], ["metric_time__week", "metric_time__month"])


def test_a_date_part_alone_is_refused(span_engine: _SpanEngine) -> None:
    """A date part with no grain: a typed error naming the span metric and the date part."""
    with pytest.raises(SpanReadError, match="'unit_days' can't be read by the date part 'month'"):
        _build_sql(
            span_engine, ["unit_days"], group_by=(TimeDimensionParameter("metric_time", date_part=DatePart.MONTH),)
        )


def test_a_date_part_with_a_grain_is_refused(span_engine: _SpanEngine) -> None:
    """A date part beside a grain would attribute each week's days to its first day's: refused."""
    with pytest.raises(SpanReadError, match="'unit_days' can't be read by the date part 'dow'"):
        _build_sql(
            span_engine,
            ["unit_days"],
            group_by=(
                TimeDimensionParameter("metric_time", grain="week"),
                TimeDimensionParameter("metric_time", date_part=DatePart.DOW),
            ),
        )


@pytest.mark.parametrize(
    "where_sql",
    (
        "{{ TimeDimension('metric_time', 'day') }} >= '2026-01-15'",
        "{{ TimeDimension('inventory_span__ds', 'day') }} >= '2026-01-15'",
        "{{ TimeDimension('metric_time', 'day') }} >= CAST(:range_from AS DATE)",
    ),
    ids=("metric_time", "agg_time_dimension", "half_the_range"),
)
def test_a_filter_on_span_time_is_refused(span_engine: _SpanEngine, where_sql: str) -> None:
    """A where-filter on the span model's time keeps or drops whole periods by their first day: refused."""
    with pytest.raises(SpanReadError, match="can't be filtered on its time"):
        _build_sql(span_engine, ["unit_days"], ["metric_time__week"], where_constraint_strs=[where_sql])


def test_a_filter_through_a_primary_entity_declared_as_an_entity_is_refused() -> None:
    """The model's own time is its time however its primary entity is declared, here as a `type: primary` entity."""
    engine = _span_engine_with(
        {
            "inventory_spans.yaml": _replaced(
                "  primary_entity: inventory_span\n\n  entities:\n",
                "  entities:\n    - name: inventory_span\n      type: primary\n",
            )
        }
    )
    with pytest.raises(SpanReadError, match="can't be filtered on its time"):
        _build_sql(
            engine,
            ["unit_days"],
            ["metric_time__week"],
            where_constraint_strs=["{{ TimeDimension('inventory_span__ds', 'day') }} >= '2026-01-15'"],
        )


def test_a_span_model_with_no_measures_is_read_and_refused_as_one() -> None:
    """A span model whose simple metric names it in its own aggregation parameters, with no measures, is a span model.

    Grouped by a grain it is read at that grain, and a time constraint on it is refused.
    """
    engine = _span_engine_with(
        {
            "inventory_spans.yaml": _replaced(
                "  measures:\n    - name: unit_days\n      expr: on_hand_units * span_days\n      agg: sum\n"
                "    - name: on_hand_units\n      agg: sum\n",
                "",
            ),
            "metrics.yaml": lambda contents: textwrap.dedent(
                """\
                ---
                metric:
                  name: unit_days
                  description: A span metric with no measure.
                  type: simple
                  type_params:
                    expr: on_hand_units * span_days
                    metric_aggregation_params:
                      semantic_model: inventory_spans
                      agg: sum
                ---
                metric:
                  name: received_units
                  description: A plain fact's sum.
                  type: simple
                  type_params:
                    measure: received_units
                """
            ),
        }
    )
    assert "generate_series(DATE_TRUNC('week'" in _build_sql(engine, ["unit_days"], ["metric_time__week"])
    with pytest.raises(SpanReadError, match="'unit_days' can't be read under a time constraint"):
        _build_sql(engine, ["unit_days"], ["metric_time__week"], time_constraint=_TIME_CONSTRAINT)


def test_the_bound_range_filter_is_read(span_engine: _SpanEngine) -> None:
    """The bound range itself, as the embedding service sends it, keeps every row of the read: accepted."""
    sql = _build_sql(
        span_engine,
        ["unit_days", "received_units"],
        ["metric_time__week"],
        where_constraint_strs=[
            "{{ TimeDimension('metric_time', 'day') }} >= CAST(:range_from AS DATE)"
            " AND {{ TimeDimension('metric_time', 'day') }} <= CAST(:range_to AS DATE)"
        ],
    )
    assert "generate_series(DATE_TRUNC('week'" in sql


def test_a_null_span_end_reads_as_open(span_engine: _SpanEngine) -> None:
    """A NULL end covers every day from its start, as upstream's validity-window join reads it.

    Without the open reading, `end > range_from` is NULL for it and the span is dropped. `test_executed_rows.py` checks
    the rows on PostgreSQL.
    """
    sql = _build_sql(span_engine, ["unit_days"], ["metric_time__week"])
    assert "(span.valid_to > CAST(:range_from AS DATE) OR span.valid_to IS NULL)" in sql
    assert "COALESCE(span.valid_to, CAST(:range_to AS DATE) + 1) > p.p_last" in sql


@pytest.mark.parametrize("fill_value", ("0) AS x; --", True, float("inf")), ids=("text", "bool", "infinity"))
def test_a_derived_fill_that_is_not_a_finite_number_is_refused(fill_value: object) -> None:
    """The derived fill is written into the SQL as text, so a value that isn't a finite number raises.

    Validation refuses such a value first (`test_derived_fill_validation.py`). This is the backstop for a manifest
    that skipped validation: the value is set after the manifest is loaded.
    """
    manifest = mf_load_manifest_from_yaml_directory(
        _SPAN_MANIFEST_DIRECTORY, template_mapping={"source_schema": _SOURCE_SCHEMA}
    )
    unit_change = next(metric for metric in manifest.metrics if metric.name == "unit_change")
    assert unit_change.config is not None
    unit_change.config.meta["fill_nulls_with"] = fill_value
    saved = convert_semantic_model.SPAN_RANGE_SQL
    convert_semantic_model.SPAN_RANGE_SQL = _SPAN_RANGE_SQL
    try:
        with SequentialIdGenerator.id_number_space(_ID_START):
            engine = _SpanEngine(manifest)
    finally:
        convert_semantic_model.SPAN_RANGE_SQL = saved
    # Raised while the combine's columns are written, which is SQL generation (`SqlGenerationError` wraps it).
    with pytest.raises((SqlGenerationError, SemanticManifestConfigurationError)) as raised:
        _build_sql(engine, ["unit_change", "received_units"], ["metric_time__week"])
    causes: List[BaseException] = []
    error: Optional[BaseException] = raised.value
    while error is not None:
        causes.append(error)
        error = error.__cause__
    assert any(type(cause) is SemanticManifestConfigurationError for cause in causes)
    assert f"`config.meta.fill_nulls_with` as {fill_value!r}, which is not a finite number" in str(causes[-1])
