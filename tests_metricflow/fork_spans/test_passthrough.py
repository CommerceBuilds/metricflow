"""FORK: the passthrough planner writes valid SQL, and an error while generating SQL fails the render.

Upstream ships `DataflowPlanOptimization.PASSTHROUGH_METRIC_EVALUATION` disabled. The embedding service enables it on
every request, and the fork carries what makes its SQL valid:

- `dataflow_to_subquery.py`: a metric more than one source of a combine carries is selected once, as the first
  non-NULL of each carrying source's `MAX`.
- `required_column_aliases.py`: a one-row source of a combine's CROSS JOIN whose columns no consumer reads keeps one
  column, instead of the column pruner raising. Any other node with no required column raises, as upstream's does.
- `passthrough_me_planner.py`: a passthrough node passes through no metric spec whose column name another, different
  spec among its inputs also uses (`transactions`, and `transactions` read with an input filter).
- `dataflow_plan_builder.py`: a node whose sources carry such a pair reads from each source only the metric specs
  its plan edges take from it. The check spends no id, so a plan without such a pair is built as upstream builds it.

And `dataflow_to_sql.py` attempts only the requested optimization level: an error raises `SqlGenerationError`, where
upstream retried at each lower level and only logged it.

Without each fix, a query here selects one column name twice in one select (Postgres: "column reference ... is
ambiguous") or fails to generate. The module builds its own manifest and renders with the Postgres renderer directly,
so it needs no database.
"""

from __future__ import annotations

import pathlib
import re
from typing import Iterator, List, Optional, Sequence
from unittest.mock import patch

import pytest
from metricflow_semantics.dag.mf_dag import DagId
from metricflow_semantics.dag.sequential_id import SequentialIdGenerator
from metricflow_semantics.model.semantic_manifest_lookup import SemanticManifestLookup
from metricflow_semantics.query.query_parser import MetricFlowQueryParser
from metricflow_semantics.specs.dunder_column_association_resolver import DunderColumnAssociationResolver
from metricflow_semantics.sql.sql_exprs import (
    NonPercentileAggregationType,
    SqlColumnReference,
    SqlColumnReferenceExpression,
    SqlFunctionExpression,
    SqlStringExpression,
)
from metricflow_semantics.sql.sql_join_type import SqlJoinType
from metricflow_semantics.sql.sql_table import SqlTable
from metricflow_semantics.test_helpers.manifest_helpers import mf_load_manifest_from_yaml_directory

from metricflow.dataflow.builder.dataflow_plan_builder import DataflowPlanBuilder
from metricflow.dataflow.builder.source_node import SourceNodeBuilder
from metricflow.dataflow.optimizer.dataflow_optimizer_factory import DataflowPlanOptimization
from metricflow.dataset.convert_semantic_model import SemanticModelToDataSetConverter
from metricflow.plan_conversion.to_sql_plan.dataflow_to_sql import DataflowToSqlPlanConverter, SqlGenerationError
from metricflow.plan_conversion.to_sql_plan.dataflow_to_subquery import DataflowNodeToSqlSubqueryVisitor
from metricflow.protocols.sql_client import SqlEngine
from metricflow.sql.optimizer.column_pruning.column_pruner import SqlColumnPrunerOptimizer
from metricflow.sql.optimizer.optimization_levels import SqlOptimizationLevel
from metricflow.sql.render.postgres import PostgresSQLSqlPlanRenderer
from metricflow.sql.sql_plan import SqlPlan, SqlSelectColumn
from metricflow.sql.sql_select_node import SqlJoinDescription, SqlSelectStatementNode
from metricflow.sql.sql_table_node import SqlTableNode
from metricflow_semantic_interfaces.type_enums.aggregation_type import AggregationType

_MANIFEST_DIRECTORY = pathlib.Path(__file__).parent / "passthrough_manifest"
_SETUP_ID_START = 10000
_WHERE = ("{{ TimeDimension('metric_time', 'day') }} >= '2020-01-01'",)
_PASSTHROUGH = frozenset(DataflowPlanOptimization.all_optimizations())

# A metric, its last-year twin and their difference, beside a ratio and its own: each plain metric is carried by
# more than one source of a combine.
_SHARED_ACROSS_A_COMBINE: tuple[list[str], list[str]] = (
    ["transactions", "transactions_ly", "transactions_vs_ly", "atv", "atv_ly", "atv_vs_ly"],
    [],
)
# A ratio and its last-year twin with no group-by: one-row branches in a CROSS JOIN, one of them unread.
_UNREAD_CROSS_JOIN_SOURCE: tuple[list[str], list[str]] = (["atv", "atv_ly"], [])
# Per-customer ratios whose inputs carry an input filter, beside the same metrics unfiltered.
_INPUT_FILTER_BESIDE_PLAIN: tuple[list[str], list[str]] = (
    ["transactions", "net_sales", "atv", "customers", "visits_per_customer", "spend_per_customer"],
    ["customer__member_segment"],
)
_ONE_INPUT_FILTERED: tuple[list[str], list[str]] = (["transactions", "visits_per_customer"], [])
_CASES: tuple[tuple[list[str], list[str]], ...] = (
    _SHARED_ACROSS_A_COMBINE,
    _UNREAD_CROSS_JOIN_SOURCE,
    (["atv", "atv_ly"], ["metric_time__day"]),
    _INPUT_FILTER_BESIDE_PLAIN,
    _ONE_INPUT_FILTERED,
)


class _Engine:
    """The objects a test needs to build and render a plan over the passthrough manifest."""

    def __init__(self) -> None:
        manifest = mf_load_manifest_from_yaml_directory(_MANIFEST_DIRECTORY, template_mapping={"source_schema": "s"})
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
        """A new builder, with an empty cache."""
        return DataflowPlanBuilder(
            source_node_set=self.source_node_set,
            semantic_manifest_lookup=self.lookup,
            node_output_resolver=self.node_output_resolver.copy(),
            column_association_resolver=self.resolver,
            source_node_builder=self.source_node_builder,
        )


@pytest.fixture(scope="module")
def engine() -> Iterator[_Engine]:  # noqa: D103
    with SequentialIdGenerator.id_number_space(_SETUP_ID_START):
        yield _Engine()


def _render(
    engine: _Engine,
    metric_names: Sequence[str],
    group_by_names: Sequence[str],
    builder: DataflowPlanBuilder | None = None,
    optimizations: frozenset[DataflowPlanOptimization] = _PASSTHROUGH,
) -> tuple[SqlPlan, str]:
    """One render, numbered from 0 as each of the service's renders is, at the default level (O5)."""
    with SequentialIdGenerator.id_number_space(0):
        query_spec = engine.query_parser.parse_and_validate_query(
            metric_names=metric_names, group_by_names=group_by_names, where_constraint_strs=_WHERE
        ).query_spec
        plan = (builder or engine.plan_builder()).build_plan(query_spec, optimizations=optimizations)
        sql_plan = engine.to_sql.convert_to_sql_plan(
            sql_engine_type=SqlEngine.POSTGRES,
            dataflow_plan_node=plan.sink_node,
            optimization_level=SqlOptimizationLevel.default_level(),
            sql_query_plan_id=DagId.from_str("plan0_optimized"),
        ).sql_plan
        return sql_plan, PostgresSQLSqlPlanRenderer().render_sql_plan(sql_plan).sql


def _duplicate_aliases(sql_plan: SqlPlan) -> List[str]:
    """Every column alias some select in the plan names twice."""
    duplicates: List[str] = []
    seen: set[int] = set()
    stack = [sql_plan.render_node]
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        stack.extend(node.parent_nodes)
        if isinstance(node, SqlSelectStatementNode):
            aliases = [column.column_alias for column in node.select_columns]
            duplicates.extend(sorted({alias for alias in aliases if aliases.count(alias) > 1}))
    return duplicates


@pytest.mark.parametrize(("metric_names", "group_by_names"), _CASES)
def test_no_select_names_a_column_twice(
    engine: _Engine, metric_names: Sequence[str], group_by_names: Sequence[str]
) -> None:
    """Every passthrough render generates at O5, and no select in it names one column twice."""
    sql_plan, _ = _render(engine, metric_names, group_by_names)
    assert _duplicate_aliases(sql_plan) == []


def test_an_unread_cross_join_source_still_joins(engine: _Engine) -> None:
    """The one-row branch whose columns nothing reads keeps a column and stays in the CROSS JOIN."""
    _, sql = _render(engine, *_UNREAD_CROSS_JOIN_SOURCE)
    assert "CROSS JOIN" in sql


@pytest.mark.parametrize("group_by_names", ([], ["metric_time__day"]), ids=("cross_join", "full_outer_join"))
def test_a_shared_metric_reads_every_source_that_carries_it(engine: _Engine, group_by_names: Sequence[str]) -> None:
    """A metric three sources of the combine carry is the first non-NULL of the three `MAX`es, not the first's alone.

    Under a FULL OUTER JOIN, a key only a later source has leaves the first source's `MAX` NULL.
    """
    _, sql = _render(engine, _SHARED_ACROSS_A_COMBINE[0], group_by_names)
    for metric_name in ("transactions", "transactions_ly"):
        # e.g. `COALESCE(MAX(subq_15.transactions), MAX(cao_2_cte.transactions), MAX(subq_19.transactions))`
        max_of = rf"MAX\(\w+\.{metric_name}\)"
        every_source = rf"COALESCE\({max_of}, {max_of}, {max_of}\)"
        assert re.search(every_source + rf" AS {metric_name}\b", sql), metric_name


def _table_read(alias: str, aggregation_type: Optional[NonPercentileAggregationType] = None) -> SqlSelectStatementNode:
    """`SELECT <alias>.x AS x FROM s.<alias> <alias>`, or with `x` aggregated by `aggregation_type` (one row)."""
    column: SqlColumnReferenceExpression = SqlColumnReferenceExpression.create(SqlColumnReference(alias, "x"))
    return SqlSelectStatementNode.create(
        description=alias,
        select_columns=(
            SqlSelectColumn(
                expr=(
                    SqlFunctionExpression.build_expression_for_non_percentile_aggregation(aggregation_type, column)
                    if aggregation_type is not None
                    else column
                ),
                column_alias="x",
            ),
        ),
        from_source=SqlTableNode.create(SqlTable(schema_name="s", table_name=alias)),
        from_source_alias=alias,
    )


def test_an_unread_source_outside_a_combine_raises() -> None:
    """A sub-query none of whose columns are read, outside a combine's CROSS JOIN, is a pruner bug: it raises.

    `SELECT 1 AS one FROM (SELECT a.x AS x FROM s.a a) a`: before the fallback was narrowed, the sub-query kept `x`
    and the bug went unseen.
    """
    plan = SqlSelectStatementNode.create(
        description="outer",
        select_columns=(SqlSelectColumn(expr=SqlStringExpression.create("1", used_columns=()), column_alias="one"),),
        from_source=_table_read("a"),
        from_source_alias="a",
    )
    with pytest.raises(RuntimeError, match="No columns are required in this node"):
        SqlColumnPrunerOptimizer().optimize(plan)


def test_an_unread_source_of_a_cross_join_that_aggregates_rows_raises() -> None:
    """A CROSS JOIN whose select doesn't aggregate to one row (a time spine joined for `metric_time`) is not a combine.

    `SELECT a.x AS x FROM (SELECT a.x ...) a CROSS JOIN (SELECT b.x ...) b`: `b` is unread, and raises.
    """
    plan = SqlSelectStatementNode.create(
        description="outer",
        select_columns=(
            SqlSelectColumn(expr=SqlColumnReferenceExpression.create(SqlColumnReference("a", "x")), column_alias="x"),
        ),
        from_source=_table_read("a"),
        from_source_alias="a",
        join_descs=(SqlJoinDescription(_table_read("b"), "b", SqlJoinType.CROSS_JOIN),),
    )
    with pytest.raises(RuntimeError, match="No columns are required in this node"):
        SqlColumnPrunerOptimizer().optimize(plan)


def test_an_unread_one_row_source_of_a_combine_keeps_a_column() -> None:
    """The combine's shape: every column aggregates, no GROUP BY, only CROSS JOINs. The unread `b` keeps `x`."""
    plan = SqlSelectStatementNode.create(
        description="combine",
        select_columns=(
            SqlSelectColumn(
                expr=SqlFunctionExpression.build_expression_for_non_percentile_aggregation(
                    AggregationType.MAX, SqlColumnReferenceExpression.create(SqlColumnReference("a", "x"))
                ),
                column_alias="x",
            ),
        ),
        from_source=_table_read("a", AggregationType.SUM),
        from_source_alias="a",
        join_descs=(SqlJoinDescription(_table_read("b", AggregationType.SUM), "b", SqlJoinType.CROSS_JOIN),),
    )
    sql = PostgresSQLSqlPlanRenderer().render_sql_plan(SqlPlan(SqlColumnPrunerOptimizer().optimize(plan))).sql
    assert "CROSS JOIN" in sql
    assert "SUM(b.x) AS x" in sql


@pytest.mark.parametrize(("metric_names", "group_by_names"), (_INPUT_FILTER_BESIDE_PLAIN, _ONE_INPUT_FILTERED))
def test_the_input_filtered_spec_is_read_beside_the_plain_one(
    engine: _Engine, metric_names: Sequence[str], group_by_names: Sequence[str]
) -> None:
    """Both `transactions` are computed: the plain one, and the one under the per-customer ratio's input filter."""
    _, sql = _render(engine, metric_names, group_by_names)
    assert "customer_id IS NOT NULL" in sql
    assert sql.count("SUM(") >= 2


@pytest.mark.parametrize(("metric_names", "group_by_names"), _CASES)
def test_a_cold_and_a_warm_builder_render_the_same_bytes(
    engine: _Engine, metric_names: Sequence[str], group_by_names: Sequence[str]
) -> None:
    """The narrowing resolves data sets in an id space of its own, so its ids never move the output's."""
    builder = engine.plan_builder()
    _, cold = _render(engine, metric_names, group_by_names, builder)
    _, warm = _render(engine, metric_names, group_by_names, builder)
    _, other = _render(engine, metric_names, group_by_names)
    assert cold == warm == other


@pytest.mark.parametrize("optimizations", (_PASSTHROUGH, frozenset(DataflowPlanOptimization.enabled_optimizations())))
@pytest.mark.parametrize(
    ("metric_names", "group_by_names"), (_SHARED_ACROSS_A_COMBINE, (["atv", "atv_ly"], ["metric_time__day"]))
)
def test_a_plan_with_no_colliding_pair_is_built_as_upstream_builds_it(
    engine: _Engine,
    metric_names: Sequence[str],
    group_by_names: Sequence[str],
    optimizations: frozenset[DataflowPlanOptimization],
) -> None:
    """Where no two sources collide, the narrowing returns its input unchanged and spends no id."""
    _, with_check = _render(engine, metric_names, group_by_names, optimizations=optimizations)
    with patch.object(
        DataflowPlanBuilder, "_narrow_colliding_sources", lambda self, me_plan, query_node, input_nodes: input_nodes
    ):
        _, without_check = _render(engine, metric_names, group_by_names, optimizations=optimizations)
    assert with_check == without_check


def test_a_sql_generation_error_fails_the_render(engine: _Engine) -> None:
    """The requested level is the only one attempted, and its error raises typed, with the cause attached."""
    with SequentialIdGenerator.id_number_space(0):
        query_spec = engine.query_parser.parse_and_validate_query(
            metric_names=["atv"], group_by_names=[], where_constraint_strs=_WHERE
        ).query_spec
        plan = engine.plan_builder().build_plan(query_spec, optimizations=_PASSTHROUGH)
    with (
        patch.object(DataflowToSqlPlanConverter, "convert_using_specifics", side_effect=RuntimeError("boom")) as call,
        pytest.raises(SqlGenerationError) as raised,
    ):
        engine.to_sql.convert_to_sql_plan(
            sql_engine_type=SqlEngine.POSTGRES,
            dataflow_plan_node=plan.sink_node,
            optimization_level=SqlOptimizationLevel.O5,
            sql_query_plan_id=DagId.from_str("plan0_optimized"),
        )
    assert call.call_count == 1
    assert isinstance(raised.value.__cause__, RuntimeError)
    assert "O5" in str(raised.value)
