"""FORK: simple-metric branches that read one source and differ only by their metric filters are read once.

The CommerceBuilds fork's `FilterMergeOptimizer` (`DataflowPlanOptimization.FILTER_MERGE`, in `all_optimizations()`)
folds such branches into one aggregation over the rows any of their filters admit, each input as
`AGG(CASE WHEN <its own filters> THEN <expression> END)`, and each branch keeps only the groups its own filters admit
a row to. The SQL for it is written in `dataflow_to_subquery.py` (`_filter_merged_read`, `_filter_merge_projection`).

The render tests build their own manifest (`filter_merge_manifest/`) and render with the Postgres renderer directly,
so they need no database. The row tests run through upstream's harness that executes queries (DuckDB, or PostgreSQL
in the `test-postgres` target), so a `--noconftest` run skips them.
"""

from __future__ import annotations

import dataclasses
import datetime
import pathlib
import re
import types
from typing import Any, Dict, FrozenSet, Iterator, List, Optional, Sequence, Tuple, cast

import pytest
from _pytest.fixtures import FixtureRequest
from metricflow_semantics.dag.mf_dag import DagId
from metricflow_semantics.dag.sequential_id import SequentialIdGenerator
from metricflow_semantics.model.semantic_manifest_lookup import SemanticManifestLookup
from metricflow_semantics.query.query_parser import MetricFlowQueryParser
from metricflow_semantics.specs.dunder_column_association_resolver import DunderColumnAssociationResolver
from metricflow_semantics.sql.sql_bind_parameters import SqlBindParameterSet
from metricflow_semantics.sql.sql_join_type import SqlJoinType
from metricflow_semantics.test_helpers.config_helpers import MetricFlowTestConfiguration
from metricflow_semantics.test_helpers.manifest_helpers import mf_load_manifest_from_yaml_directory
from metricflow_semantics.test_helpers.time_helpers import ConfigurableTimeSource

from metricflow.dataflow.builder.dataflow_plan_builder import DataflowPlanBuilder
from metricflow.dataflow.builder.source_node import SourceNodeBuilder
from metricflow.dataflow.dataflow_plan import DataflowPlan, DataflowPlanNode
from metricflow.dataflow.nodes.aggregate_simple_metric_inputs import AggregateSimpleMetricInputsNode
from metricflow.dataflow.nodes.filter_elements import SelectorNode
from metricflow.dataflow.nodes.join_to_base import JoinOnEntitiesNode
from metricflow.dataflow.nodes.where_filter import WhereFilterNode
from metricflow.dataflow.optimizer.dataflow_optimizer_factory import DataflowPlanOptimization
from metricflow.dataflow.optimizer.filter_merge_optimizer import FilterMergeOptimizer
from metricflow.dataset import convert_semantic_model
from metricflow.dataset.convert_semantic_model import SemanticModelToDataSetConverter
from metricflow.engine.metricflow_engine import MetricFlowEngine, MetricFlowQueryRequest
from metricflow.plan_conversion.to_sql_plan.dataflow_to_sql import DataflowToSqlPlanConverter
from metricflow.plan_conversion.to_sql_plan.dataflow_to_subquery import DataflowNodeToSqlSubqueryVisitor
from metricflow.protocols.sql_client import SqlEngine
from metricflow.sql.optimizer.optimization_levels import SqlOptimizationLevel
from metricflow.sql.render.postgres import PostgresSQLSqlPlanRenderer
from metricflow_semantic_interfaces.test_utils import as_datetime
from tests_metricflow.fixtures.sql_clients.ddl_sql_client import SqlClientWithDDLMethods
from tests_metricflow.fork_spans import test_span_rendering

_MANIFEST_DIRECTORY = pathlib.Path(__file__).parent / "filter_merge_manifest"
_SETUP_ID_START = 10000
_WHERE = ("{{ TimeDimension('metric_time', 'day') }} >= '2020-01-01'",)
_ALL = frozenset(DataflowPlanOptimization.all_optimizations())
_UNMERGED = frozenset(_ALL - {DataflowPlanOptimization.FILTER_MERGE})
_ENABLED = frozenset(DataflowPlanOptimization.enabled_optimizations())
# The comment MetricFlow writes on the merged read's select.
_MERGED_READ = "Aggregate Inputs for Simple Metrics, filters merged"

# Three members with filters of their own (`comparable_sales`'s on the store, so only its branch joins the stores),
# two of them also a distinct count: one read, its WHERE the OR of the three.
_FILTERED_ONLY = ("web_sales", "return_sales", "comparable_sales", "web_customers", "return_customers")
# The same beside `sales`, which has no filter of its own: one read, no OR.
_WITH_AN_UNFILTERED_MEMBER = _FILTERED_ONLY + ("sales",)


class _Engine:
    """The objects a test needs to build and render a plan over `filter_merge_manifest/`."""

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

    def plan(
        self,
        metric_names: Sequence[str],
        group_by_names: Sequence[str],
        optimizations: FrozenSet[DataflowPlanOptimization] = _ALL,
        where: Sequence[str] = _WHERE,
    ) -> DataflowPlan:
        """One plan, built with a new builder, under the request's filters `where`."""
        query_spec = self.query_parser.parse_and_validate_query(
            metric_names=metric_names, group_by_names=group_by_names, where_constraint_strs=where or None
        ).query_spec
        builder = DataflowPlanBuilder(
            source_node_set=self.source_node_set,
            semantic_manifest_lookup=self.lookup,
            node_output_resolver=self.node_output_resolver.copy(),
            column_association_resolver=self.resolver,
            source_node_builder=self.source_node_builder,
        )
        return builder.build_plan(query_spec, optimizations=optimizations)

    def render(
        self,
        metric_names: Sequence[str],
        group_by_names: Sequence[str],
        optimizations: FrozenSet[DataflowPlanOptimization] = _ALL,
        where: Sequence[str] = _WHERE,
    ) -> str:
        """One render with a new builder, numbered from 0 as each of an embedding service's renders is, at O5."""
        with SequentialIdGenerator.id_number_space(0):
            plan = self.plan(metric_names, group_by_names, optimizations, where)
            sql_plan = self.to_sql.convert_to_sql_plan(
                sql_engine_type=SqlEngine.POSTGRES,
                dataflow_plan_node=plan.sink_node,
                optimization_level=SqlOptimizationLevel.default_level(),
                sql_query_plan_id=DagId.from_str("plan0"),
            ).sql_plan
            return PostgresSQLSqlPlanRenderer().render_sql_plan(sql_plan).sql


@pytest.fixture(scope="module")
def engine() -> Iterator[_Engine]:  # noqa: D103
    with SequentialIdGenerator.id_number_space(_SETUP_ID_START):
        yield _Engine()


def _merged_read_ctes(sql: str) -> List[str]:
    """The header line of each CTE that is a merged read, e.g. `WITH am_9_cte AS (`."""
    headers = re.findall(r"^(?:WITH |, )?(\w+_cte AS (?:NOT MATERIALIZED )?\()\n\s*-- (.*)$", sql, flags=re.MULTILINE)
    return [header for header, description in headers if description == _MERGED_READ]


@pytest.mark.parametrize("group_by_names", (["store__region"], ["metric_time__day"], []), ids=("region", "day", "none"))
@pytest.mark.parametrize(
    "metric_names", (_FILTERED_ONLY, _WITH_AN_UNFILTERED_MEMBER), ids=("filtered_only", "with_an_unfiltered_member")
)
def test_branches_that_differ_only_by_their_filters_are_read_once(
    engine: _Engine, metric_names: Sequence[str], group_by_names: Sequence[str]
) -> None:
    """One merged read of the sales lines, where unmerged each filter text is a read of its own."""
    merged = engine.render(metric_names, group_by_names)
    unmerged = engine.render(metric_names, group_by_names, _UNMERGED)
    assert len(_merged_read_ctes(merged)) == 1
    assert _MERGED_READ not in unmerged
    # Each filter text is a WHERE of its own without the merge, and only inside its members' aggregates with it.
    for own_filter in ("line__channel = 'web'", "line__is_return = true", "store__is_comparable = true"):
        assert re.search(rf"WHERE \(?{re.escape(own_filter)}", unmerged)
        assert f"SUM(CASE WHEN ({own_filter}) THEN " in merged
    assert "COUNT(DISTINCT CASE WHEN (line__channel = 'web') THEN " in merged
    assert "COUNT(DISTINCT CASE WHEN (line__is_return = true) THEN " in merged
    # The merged read's WHERE takes the OR of the members' own filters, only when every member has one.
    has_or = re.search(r"\) OR \(\(", merged) is not None
    assert has_or == ("sales" not in metric_names)


@pytest.mark.parametrize("group_by_names", (["store__region"], []), ids=("region", "none"))
def test_a_member_with_no_filter_merges_under_a_request_with_none(
    engine: _Engine, group_by_names: Sequence[str]
) -> None:
    """With no filter in the request, `sales` has no WHERE at all, and still shares one read with `web_sales`.

    The merged read has no WHERE either: `sales` reads every row, and `web_sales` its own inside its aggregate.
    """
    merged = engine.render(["sales", "web_sales"], group_by_names, where=())
    assert _MERGED_READ not in engine.render(["sales", "web_sales"], group_by_names, _UNMERGED, where=())
    assert len(_merged_read_ctes(merged)) == 1
    assert "SUM(CASE WHEN (line__channel = 'web') THEN " in merged
    assert "WHERE" not in merged.split(_MERGED_READ, 1)[1].split("\n)\n", 1)[0]


@pytest.mark.parametrize(
    ("group_by_names", "flagged"),
    ((["store__region"], True), (["metric_time__day"], True), ([], False)),
    ids=("region", "day", "none"),
)
def test_a_grouped_member_keeps_only_the_groups_its_own_filters_admit_a_row_to(
    engine: _Engine, group_by_names: Sequence[str], flagged: bool
) -> None:
    """Grouped, each filtered member counts its rows and its projection drops a group where it counts none.

    So a member whose filter admits no row in a group has no row there, as its own branch had none, and the combine's
    full join gives it NULL in that group, a distinct count included. Ungrouped, every branch is one row and keeps it,
    so a distinct count over no rows reads 0 there, as unmerged.
    """
    sql = engine.render(_WITH_AN_UNFILTERED_MEMBER, group_by_names)
    flags = re.findall(r"SUM\(CASE WHEN \(.*?\) THEN 1 END\) AS (__fm0_\d+_has)", sql)
    if flagged:
        # One flag per filtered member (web, return, comparable), none for `sales`.
        assert len(flags) == 3
        for flag in flags:
            assert f"WHERE {flag} > 0" in sql
    else:
        assert flags == []
        assert "_has > 0" not in sql


def test_a_member_whose_filter_needs_a_join_the_others_dont(engine: _Engine) -> None:
    """The merged read joins the stores once, as a LEFT OUTER join, so no other member gains or loses a row."""
    merged = engine.render(["web_sales", "comparable_sales"], ["metric_time__day"])
    unmerged = engine.render(["web_sales", "comparable_sales"], ["metric_time__day"], _UNMERGED)
    assert len(_merged_read_ctes(merged)) == 1
    assert re.findall(r"(\w+ \w+ JOIN|\w+ JOIN)\s+s\.fork_fm_stores", merged) == ["LEFT OUTER JOIN"]
    assert re.findall(r"(\w+ \w+ JOIN|\w+ JOIN)\s+s\.fork_fm_stores", unmerged) == ["LEFT OUTER JOIN"]


# A request filter on a group-by metric: each branch joins `store` twice, to the stores' model for the region and to
# the subquery that computes `sales` by store.
_GROUP_BY_METRIC_FILTER = "{{ Metric('sales', group_by=['store']) }} > 10"


def test_a_group_by_metric_joined_beside_a_dimension_merges(engine: _Engine) -> None:
    """Both joins on `store` are kept, each once, and the fact is read once.

    The subquery that computes `sales` by store is built in each branch; the copies fold into one read inside the
    merged read of `web_sales` and `return_sales`, instead of that read keeping the unmerged copies.
    """
    where = (_GROUP_BY_METRIC_FILTER,)
    merged = engine.render(["web_sales", "return_sales"], ["store__region"], where=where)
    unmerged = engine.render(["web_sales", "return_sales"], ["store__region"], _UNMERGED, where=where)
    assert _MERGED_READ not in unmerged
    assert len(_merged_read_ctes(merged)) == 1
    assert "WHERE (\n      store__sales > 10\n    ) AND (" in merged
    assert merged.count("FROM s.fork_fm_stores") == 1
    # One aggregation of `sales` by store, inside the merged read.
    assert len(re.findall(r"SUM\(__sales\) AS store__sales", merged)) == 1
    assert merged.count("FROM s.fork_fm_sales_lines") == 1


def test_a_merge_under_a_merged_read_is_kept_there(engine: _Engine) -> None:
    """The subquery computing `sales` by store, merged, is the one both the merged read and an unmerged branch join.

    `web_sales` and `comparable_sales` share one read; `return_median_amount` keeps its own. All three join the
    subquery, whose copies fold into one read, so `sales` is aggregated by store once, not again inside the merged read.
    """
    where = (_GROUP_BY_METRIC_FILTER,)
    metric_names = ["web_sales", "comparable_sales", "return_median_amount"]
    merged = engine.render(metric_names, ["store__region"], where=where)
    unmerged = engine.render(metric_names, ["store__region"], _UNMERGED, where=where)

    def aggregations_by_store(sql: str) -> int:
        return len(re.findall(r"^\s*GROUP BY\n\s*store$", sql, flags=re.MULTILINE))

    assert aggregations_by_store(unmerged) == 3
    assert aggregations_by_store(merged) == 1


def test_a_branch_with_any_other_join_keeps_the_unmerged_plan(engine: _Engine) -> None:
    """A branch whose entity join is not LEFT OUTER is not folded: such a join could drop or add rows.

    MetricFlow plans a simple metric's entity joins LEFT OUTER, so no request here makes another kind: the test
    rebuilds `comparable_sales`'s own branch with its join made INNER, and asks the optimizer whether it would fold it.
    """
    plan = engine.plan(["web_sales", "comparable_sales"], ["metric_time__day"], _UNMERGED)
    nodes: List[DataflowPlanNode] = []
    stack: List[DataflowPlanNode] = [plan.sink_node]
    while stack:
        node = stack.pop()
        nodes.append(node)
        stack.extend(node.parent_nodes)
    # Each branch: aggregate <- kept <- where <- pre <- (join) <- source; `comparable_sales`'s alone has the join.
    branches: List[Tuple[DataflowPlanNode, ...]] = []
    for node in nodes:
        if isinstance(node, AggregateSimpleMetricInputsNode):
            chain: List[DataflowPlanNode] = [node]
            for _ in range(4):
                chain.append(chain[-1].parent_nodes[0])
            branches.append(tuple(chain))
    joined = [branch for branch in branches if isinstance(branch[-1], JoinOnEntitiesNode)]
    assert len(joined) == 1
    aggregate, kept, where, pre, join = joined[0]
    assert isinstance(join, JoinOnEntitiesNode)
    consumers = [node for node in nodes if aggregate in node.parent_nodes]
    optimizer = FilterMergeOptimizer(engine.lookup.manifest_object_lookup)
    assert optimizer._as_branch(aggregate, consumers) is not None

    inner_join = JoinOnEntitiesNode.create(
        left_node=join.left_node,
        join_targets=[dataclasses.replace(target, join_type=SqlJoinType.INNER) for target in join.join_targets],
    )
    inner_aggregate = aggregate.with_new_parents(
        [kept.with_new_parents([where.with_new_parents([pre.with_new_parents([inner_join])])])]
    )
    assert optimizer._as_branch(inner_aggregate, consumers) is None


@pytest.mark.parametrize(("return_value", "merges"), ((1, True), (2, False)), ids=("agree", "conflict"))
def test_branches_whose_bound_values_conflict_are_not_grouped(
    engine: _Engine, return_value: int, merges: bool
) -> None:
    """Two members that bind one key to different values keep their own reads, and the optimizer raises nothing.

    The merged read's WHERE binds every member's values at once, so it can't hold two values for one key. No request
    here binds a value, so the test gives each member's own filter one, `web_sales`'s `1` and `return_sales`'s
    `return_value`.
    """
    plan = engine.plan(["web_sales", "return_sales"], ["store__region"], _UNMERGED)
    replaced: Dict[int, DataflowPlanNode] = {}

    def rebuild(node: DataflowPlanNode) -> DataflowPlanNode:
        if id(node) in replaced:
            return replaced[id(node)]
        parents = [rebuild(parent) for parent in node.parent_nodes]
        result = node.with_new_parents(parents) if parents else node
        if isinstance(result, WhereFilterNode):
            specs = []
            for spec in result.filter_specs:
                for text, value in (("line__channel", 1), ("line__is_return", return_value)):
                    if text in spec.where_sql:
                        spec = dataclasses.replace(
                            spec, bind_parameters=SqlBindParameterSet.create_from_dict({"abp_member": value})
                        )
                specs.append(spec)
            result = WhereFilterNode.create(parent_node=result.parent_node, filter_specs=specs)
        replaced[id(node)] = result
        return result

    bound = DataflowPlan(sink_nodes=[rebuild(plan.sink_node)], plan_id=DagId.from_str("bound"))
    optimized = FilterMergeOptimizer(engine.lookup.manifest_object_lookup).optimize(bound)
    merged_reads = [
        node
        for node in FilterMergeOptimizer._all_nodes(optimized.sink_node)
        if isinstance(node, AggregateSimpleMetricInputsNode)
        and node.filter_merge is not None
        and node.filter_merge.member is None
    ]
    assert len(merged_reads) == (1 if merges else 0)


@pytest.mark.parametrize(("distinct", "targets"), (((False, False), 1), ((False, True), 2)), ids=("plain", "distinct"))
def test_join_selectors_merge_only_when_they_agree_on_distinct(
    engine: _Engine, distinct: Tuple[bool, bool], targets: int
) -> None:
    """Two members' selectors over one joined node become one selector only if both are DISTINCT or neither is.

    Merged, a DISTINCT selector would lose its de-duplication, and the join could then add rows. No entity join makes
    a DISTINCT selector, so the test builds the two join targets itself.
    """
    plan = engine.plan(["comparable_sales"], ["metric_time__day"], _UNMERGED)
    joins = [node for node in FilterMergeOptimizer._all_nodes(plan.sink_node) if isinstance(node, JoinOnEntitiesNode)]
    assert len(joins) == 1
    target = joins[0].join_targets[0]
    selector = target.join_node
    assert isinstance(selector, SelectorNode)
    branches = []
    for is_distinct in distinct:
        join_node = SelectorNode.create(
            parent_node=selector.parent_node, include_specs=selector.include_specs, distinct=is_distinct
        )
        join = JoinOnEntitiesNode.create(
            left_node=joins[0].left_node, join_targets=[dataclasses.replace(target, join_node=join_node)]
        )
        branches.append(types.SimpleNamespace(join=join))
    merged = FilterMergeOptimizer._merged_join_targets(cast(Sequence[Any], branches))
    assert merged is not None
    assert len(merged) == targets


def test_the_merged_read_stays_materialized(engine: _Engine) -> None:
    """The merged read aggregates, so the Postgres renderer's row-level check leaves its CTE materialized.

    Several projections read it; inlined, Postgres would aggregate the fact again for each.
    """
    sql = engine.render(_WITH_AN_UNFILTERED_MEMBER, ["store__region"])
    headers = _merged_read_ctes(sql)
    assert len(headers) == 1
    assert "NOT MATERIALIZED" not in headers[0]
    # It is read by each member's projection: three filtered members and `sales`.
    cte_name = headers[0].split(" ")[0]
    assert len(re.findall(rf"(?:FROM|JOIN)\s+{cte_name}\b", sql)) == 4


# Each shape the merge leaves to the unmerged plan, with two metrics of that shape under different filters on one model.
_EXCLUDED_SHAPES: Tuple[Tuple[str, Sequence[str], Sequence[str]], ...] = (
    ("another_aggregation", ("web_median_amount", "return_median_amount"), ("store__region",)),
    ("a_time_spine_join", ("web_sales_on_the_spine", "return_sales_on_the_spine"), ("metric_time__day",)),
    ("an_offset", ("web_sales_a_week_ago", "return_sales_a_week_ago"), ("metric_time__day",)),
    ("a_cumulative_window", ("web_sales_to_date", "return_sales_to_date"), ("metric_time__day",)),
    ("a_cumulative_metric_ungrouped", ("web_sales_to_date", "return_sales_to_date"), ()),
    ("a_semi_additive_join", ("card_balance", "cash_balance"), ("metric_time__day",)),
    ("a_conversion_step", ("web_visit_conversions", "store_visit_conversions"), ("metric_time__day",)),
)


@pytest.mark.parametrize(
    ("metric_names", "group_by_names"),
    tuple((metric_names, group_by_names) for _, metric_names, group_by_names in _EXCLUDED_SHAPES),
    ids=tuple(name for name, _, _ in _EXCLUDED_SHAPES),
)
def test_each_excluded_shape_keeps_the_unmerged_plan(
    engine: _Engine, metric_names: Sequence[str], group_by_names: Sequence[str]
) -> None:
    """Byte for byte the SQL rendered without the merge."""
    merged = engine.render(metric_names, group_by_names)
    assert _MERGED_READ not in merged
    assert merged == engine.render(metric_names, group_by_names, _UNMERGED)


def test_an_excluded_member_stays_out_and_the_others_merge(engine: _Engine) -> None:
    """A median beside two sums under other filters keeps its own read; the two sums share one.

    (A median under the filter of a sum shares that sum's branch, which then keeps the unmerged plan whole.)
    """
    sql = engine.render(["web_sales", "comparable_sales", "return_median_amount"], ["store__region"])
    assert len(_merged_read_ctes(sql)) == 1
    assert "SUM(CASE WHEN (line__channel = 'web') THEN " in sql
    assert "SUM(CASE WHEN (store__is_comparable = true) THEN " in sql
    assert "CASE WHEN (line__is_return = true)" not in sql
    assert "PERCENTILE_CONT(0.5)" in sql


@pytest.fixture(scope="module")
def span_engine_for_merge() -> Iterator[test_span_rendering._SpanEngine]:
    """The span manifest's engine objects, built with the range set, as `test_span_rendering` builds them."""
    saved = convert_semantic_model.SPAN_RANGE_SQL
    convert_semantic_model.SPAN_RANGE_SQL = test_span_rendering._SPAN_RANGE_SQL
    try:
        with SequentialIdGenerator.id_number_space(test_span_rendering._ID_START):
            yield test_span_rendering._SpanEngine()
    finally:
        convert_semantic_model.SPAN_RANGE_SQL = saved


@pytest.mark.parametrize(
    "group_by_name", ("location", "metric_time__week", "metric_time__fiscal_month"), ids=("no_grain", "week", "fiscal")
)
def test_span_branches_at_a_grain_share_one_read(
    span_engine_for_merge: test_span_rendering._SpanEngine, group_by_name: str
) -> None:
    """The last-day and first-day branches of one span model fold into one read, with or without a grain.

    `DataflowPlanBuilder._span_read_at_grain` keeps one read per span model and grain, but builds a new metric-time
    node over it for each branch, so the two branches' sources are different objects that build the same rows. The
    merge groups sources by what they build, not by object, so they still fold.
    """
    sql = test_span_rendering._build_sql(span_engine_for_merge, ["ending_units", "beginning_units"], [group_by_name])
    assert len(_merged_read_ctes(sql)) == 1
    assert sql.count("FROM span_test.fct_inventory_spans") == 1
    assert "SUM(CASE WHEN (inventory_span__span_is_last = 1) THEN " in sql
    assert "SUM(CASE WHEN (inventory_span__span_is_first = 1) THEN " in sql


# Rows, executed.

# Each metric's value by group: a group's key as text (a day `2020-01-06`, a region, `None` for no region, or `` with
# no group-by) mapped to each metric's value, `None` for NULL.
_Rows = Dict[str, Dict[str, Optional[float]]]

# The sales lines (line, store, customer, day, channel, return, amount):
#   1 s1 c1   2020-01-06 web   no  10        s1 east, comparable
#   2 s1 c2   2020-01-06 store no  20        s2 west, not comparable
#   3 s2 c1   2020-01-07 store yes  5        s3 north, comparable
#   4 s2 c3   2020-01-07 store no   7        s9 no store row: its lines join no store, so they have no region
#   5 s3 c4   2020-01-08 web   no   3
#   6 s3 NULL 2020-01-08 store yes  4
#   7 s9 c5   2020-01-09 web   no   8
_LINES = (
    (1, "s1", "c1", "2020-01-06", "web", "false", 10),
    (2, "s1", "c2", "2020-01-06", "store", "false", 20),
    (3, "s2", "c1", "2020-01-07", "store", "true", 5),
    (4, "s2", "c3", "2020-01-07", "store", "false", 7),
    (5, "s3", "c4", "2020-01-08", "web", "false", 3),
    (6, "s3", None, "2020-01-08", "store", "true", 4),
    (7, "s9", "c5", "2020-01-09", "web", "false", 8),
)
_STORES = (("s1", "east", "true"), ("s2", "west", "false"), ("s3", "north", "true"))

_METRICS = ("web_sales", "return_sales", "comparable_sales", "web_customers", "return_customers", "sales")


def _row(*values: Optional[float]) -> Dict[str, Optional[float]]:
    return dict(zip(_METRICS, values))


# By region: a member whose filter admits no row in a group reads NULL there (east has no return; west no web line
# and no comparable store), a distinct count too (`return_customers` in east). North's one return has no customer:
# its group has a row, so its distinct count reads 0. The lines of s9 join no store: their region is NULL, and only
# `comparable_sales` needs the store's columns to filter them, so the others still count them.
_BY_REGION: _Rows = {
    "east": _row(10, None, 30, 1, None, 30),
    "west": _row(None, 5, None, None, 1, 12),
    "north": _row(3, 4, 7, 1, 0, 7),
    "None": _row(8, None, None, 1, None, 8),
}
_BY_DAY: _Rows = {
    "2020-01-06": _row(10, None, 30, 1, None, 30),
    "2020-01-07": _row(None, 5, None, None, 1, 12),
    "2020-01-08": _row(3, 4, 7, 1, 0, 7),
    "2020-01-09": _row(8, None, None, 1, None, 8),
}
_UNGROUPED: _Rows = {"": _row(21, 9, 37, 3, 1, 57)}
# Ungrouped over east's lines only: no return there, so `return_sales` reads NULL and `return_customers` 0, as an
# ungrouped distinct count over no rows always has.
_UNGROUPED_EAST: _Rows = {"": _row(10, None, 30, 1, 0, 30)}
# Only stores whose `sales` is over 10: s1 (30) and s2 (12), not s3 (7) or s9 (8).
_BY_REGION_OVER_10: _Rows = {"east": _BY_REGION["east"], "west": _BY_REGION["west"]}


@pytest.fixture
def executing_sql_client(request: FixtureRequest) -> SqlClientWithDDLMethods:
    """Upstream's session SQL client, which can also run DDL. Skips under `--noconftest`, which leaves it out."""
    if request.config.getoption("noconftest"):
        pytest.skip("Executes queries, so it needs upstream's `ddl_sql_client` fixture, left out by `--noconftest`.")
    return request.getfixturevalue("ddl_sql_client")


@pytest.fixture
def merge_engine(request: FixtureRequest, executing_sql_client: SqlClientWithDDLMethods) -> Iterator[MetricFlowEngine]:
    """An engine over `filter_merge_manifest/` and the tables above, in a schema of the test's own, dropped after it."""
    configuration: MetricFlowTestConfiguration = request.getfixturevalue("mf_test_configuration")
    schema_name = f"{configuration.mf_system_schema}_fork_fm"
    executing_sql_client.create_schema(schema_name)
    try:
        tables = {
            "fork_fm_sales_lines": (
                "line_id INTEGER, store_id VARCHAR, customer_id VARCHAR, ds TIMESTAMP, channel VARCHAR,"
                " is_return BOOLEAN, amount INTEGER, units INTEGER",
                tuple(
                    f"{line}, '{store}', {'NULL' if customer is None else repr(customer)},"
                    f" CAST('{day}' AS TIMESTAMP), '{channel}', {is_return}, {amount}, 1"
                    for line, store, customer, day, channel, is_return, amount in _LINES
                ),
            ),
            "fork_fm_stores": (
                "store_id VARCHAR, region VARCHAR, is_comparable BOOLEAN",
                tuple(f"'{store}', '{region}', {comparable}" for store, region, comparable in _STORES),
            ),
            "fork_fm_time_spine": (
                "ds TIMESTAMP",
                tuple(
                    f"CAST('{(datetime.date(2020, 1, 1) + datetime.timedelta(days=offset)).isoformat()}' AS TIMESTAMP)"
                    for offset in range(31)
                ),
            ),
        }
        for table, (columns, rows) in tables.items():
            executing_sql_client.execute(f"DROP TABLE IF EXISTS {schema_name}.{table}")
            executing_sql_client.execute(f"CREATE TABLE {schema_name}.{table} ({columns})")
            executing_sql_client.execute(
                f"INSERT INTO {schema_name}.{table} VALUES {', '.join(f'({row})' for row in rows)}"
            )
        manifest = mf_load_manifest_from_yaml_directory(
            _MANIFEST_DIRECTORY, template_mapping={"source_schema": schema_name}
        )
        yield MetricFlowEngine(
            semantic_manifest_lookup=SemanticManifestLookup(manifest),
            sql_client=executing_sql_client,
            column_association_resolver=DunderColumnAssociationResolver(),
            time_source=ConfigurableTimeSource(as_datetime("2020-01-01")),
        )
    finally:
        executing_sql_client.drop_schema(schema_name, cascade=True)


def _rows(
    engine: MetricFlowEngine,
    group_by_names: Sequence[str],
    where: Sequence[str],
    optimizations: FrozenSet[DataflowPlanOptimization],
) -> Tuple[_Rows, str]:
    """The query's rows by group, and the SQL it ran."""
    request = MetricFlowQueryRequest.create(
        metric_names=_METRICS,
        group_by_names=group_by_names,
        where_constraints=list(where),
        dataflow_plan_optimizations=set(optimizations),
    )
    sql = engine.explain(request).sql_statement.sql
    result = engine.query(request).result_df
    assert result is not None
    rows: _Rows = {}
    for row in result.rows:
        key = ""
        if group_by_names:
            group = row[result.column_name_index(group_by_names[0])]
            # A day is a `datetime`; its date alone names the group.
            key = str(group)[:10] if group is not None else "None"
        assert key not in rows, f"group {key!r} twice in {group_by_names}"
        rows[key] = {}
        for metric_name in _METRICS:
            value = row[result.column_name_index(metric_name)]
            rows[key][metric_name] = None if value is None else float(str(value))
    return rows, sql


@pytest.mark.parametrize(
    ("group_by_names", "where", "expected"),
    (
        (("store__region",), _WHERE, _BY_REGION),
        (("metric_time__day",), _WHERE, _BY_DAY),
        ((), _WHERE, _UNGROUPED),
        ((), _WHERE + ("{{ Dimension('store__region') }} = 'east'",), _UNGROUPED_EAST),
        (("store__region",), (), _BY_REGION),
        ((), (), _UNGROUPED),
        (("store__region",), (_GROUP_BY_METRIC_FILTER,), _BY_REGION_OVER_10),
    ),
    ids=(
        "by_region",
        "by_day",
        "ungrouped",
        "ungrouped_east",
        "by_region_no_filter",
        "ungrouped_no_filter",
        "by_region_group_by_metric",
    ),
)
def test_a_merged_read_returns_the_unmerged_plans_rows(
    merge_engine: MetricFlowEngine, group_by_names: Sequence[str], where: Sequence[str], expected: _Rows
) -> None:
    """The merged read's rows equal the plan's without the merge, and upstream's default plan's, row for row.

    Executed, on the database the session runs (DuckDB or PostgreSQL).
    """
    merged, merged_sql = _rows(merge_engine, group_by_names, where, _ALL)
    assert _MERGED_READ in merged_sql, "the query must have run the merged read"
    unmerged, unmerged_sql = _rows(merge_engine, group_by_names, where, _UNMERGED)
    assert _MERGED_READ not in unmerged_sql
    upstream_default, _ = _rows(merge_engine, group_by_names, where, _ENABLED)
    assert merged == expected
    assert unmerged == expected
    assert upstream_default == expected
