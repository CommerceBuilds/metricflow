"""FORK: a source-node recipe search spends its ids in a space of its own, and none of them names a CTE.

`DataflowPlanBuilder._find_source_node_recipe` runs the uncached search inside
`SequentialIdGenerator.id_number_space(RECIPE_SEARCH_ID_START)`. Without it, the ids a search spends advance the
counters the output continues from, so the same request numbered its `subq_N` aliases differently on a cache miss
(the first render) and a hit (every later one). With it, a node a recipe keeps carries an id from that space, every
search starts the space at the same value, and two such nodes can share an id; so `DataflowNodeToSqlCteVisitor`
names the CTE of such a node from its own per-conversion count (`_cte_alias`), never from its id.

The module builds its own manifest (a dimension two hops from the fact, and a derived metric whose filtered input
forces a second search) and renders with the Postgres renderer directly, so it needs no database.
"""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass
from typing import Iterator, List, Sequence

import pytest
from metricflow_semantics.dag.mf_dag import DagId, NodeId
from metricflow_semantics.dag.sequential_id import RECIPE_SEARCH_ID_START, SequentialIdGenerator
from metricflow_semantics.model.semantic_manifest_lookup import SemanticManifestLookup
from metricflow_semantics.query.query_parser import MetricFlowQueryParser
from metricflow_semantics.specs.dunder_column_association_resolver import DunderColumnAssociationResolver
from metricflow_semantics.test_helpers.manifest_helpers import mf_load_manifest_from_yaml_directory

from metricflow.dataflow.builder.dataflow_plan_builder import DataflowPlanBuilder
from metricflow.dataflow.builder.source_node import SourceNodeBuilder
from metricflow.dataflow.dataflow_plan import DataflowPlanNode
from metricflow.dataflow.optimizer.dataflow_optimizer_factory import DataflowPlanOptimization
from metricflow.dataset.convert_semantic_model import SemanticModelToDataSetConverter
from metricflow.plan_conversion.to_sql_plan.dataflow_to_cte import DataflowNodeToSqlCteVisitor
from metricflow.plan_conversion.to_sql_plan.dataflow_to_sql import DataflowToSqlPlanConverter
from metricflow.plan_conversion.to_sql_plan.dataflow_to_subquery import DataflowNodeToSqlSubqueryVisitor
from metricflow.protocols.sql_client import SqlEngine
from metricflow.sql.optimizer.optimization_levels import SqlOptimizationLevel
from metricflow.sql.render.postgres import PostgresSQLSqlPlanRenderer

_MANIFEST_DIRECTORY = pathlib.Path(__file__).parent / "recipe_manifest"
_TWO_HOPS = "account_id__customer_id__customer_name"
# The engine's setup objects are numbered from here, as the service's are; each render from 0.
_SETUP_ID_START = 10000


class _Engine:
    """The objects a test needs to build and render a plan over the recipe manifest."""

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
        """A new builder, with an empty recipe cache."""
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


@dataclass(frozen=True)
class _Render:
    sql: str
    recipe_space_node_ids: List[str]


def _index(node_id: NodeId) -> int:
    return int(node_id.id_str.rpartition("_")[2])


def _render(engine: _Engine, builder: DataflowPlanBuilder, metric_names: Sequence[str]) -> _Render:
    """One render on `builder`, numbered from 0 as each of the service's renders is, at the default level (O5)."""
    with SequentialIdGenerator.id_number_space(0):
        query_spec = engine.query_parser.parse_and_validate_query(
            metric_names=metric_names, group_by_names=[_TWO_HOPS]
        ).query_spec
        plan = builder.build_plan(query_spec, optimizations=DataflowPlanOptimization.enabled_optimizations())
        sql_plan = engine.to_sql.convert_to_sql_plan(
            sql_engine_type=SqlEngine.POSTGRES,
            dataflow_plan_node=plan.sink_node,
            optimization_level=SqlOptimizationLevel.default_level(),
            sql_query_plan_id=DagId.from_str("plan0_optimized"),
        ).sql_plan
        seen: dict[int, DataflowPlanNode] = {}
        stack: List[DataflowPlanNode] = [plan.sink_node]
        while stack:
            node = stack.pop()
            if id(node) not in seen:
                seen[id(node)] = node
                stack.extend(node.parent_nodes)
        return _Render(
            sql=PostgresSQLSqlPlanRenderer().render_sql_plan(sql_plan).sql,
            recipe_space_node_ids=sorted(
                node.node_id.id_str for node in seen.values() if _index(node.node_id) >= RECIPE_SEARCH_ID_START
            ),
        )


@pytest.mark.parametrize("metric_names", (["txn_total"], ["txn_share_of_month"], ["txn_share_of_month", "txn_total"]))
def test_a_cache_miss_and_a_hit_render_the_same_bytes(engine: _Engine, metric_names: Sequence[str]) -> None:
    """A cache miss, a cache hit and another builder render the same SQL.

    The first render runs the search and the second reads its recipe from the cache; the search's ids never reach
    the counters the output continues from.
    """
    builder = engine.plan_builder()
    miss = _render(engine, builder, metric_names)
    hit = _render(engine, builder, metric_names)
    other = _render(engine, engine.plan_builder(), metric_names)
    assert miss.sql == hit.sql == other.sql
    # The search's nodes are in the plan: the test renders the path the fork changed.
    assert miss.recipe_space_node_ids


def test_two_searches_in_one_render_keep_nodes_with_one_id(engine: _Engine) -> None:
    """The case `_cte_alias` exists for: two searches in one render each keep a node, numbered from the same start."""
    ids = _render(engine, engine.plan_builder(), ["txn_share_of_month"]).recipe_space_node_ids
    assert len(ids) > len(set(ids)), ids


@pytest.mark.parametrize("metric_names", (["txn_total"], ["txn_share_of_month"], ["txn_share_of_month", "txn_total"]))
def test_no_cte_alias_carries_a_recipe_search_id(engine: _Engine, metric_names: Sequence[str]) -> None:
    """No CTE alias carries an id from the recipe search's space.

    Every alias is upstream's `<node id>_cte` for a node numbered outside that space, or the fork's
    `<prefix>_recipe_<n>_cte`.
    """
    sql = _render(engine, engine.plan_builder(), metric_names).sql
    for alias in re.findall(r"(\w+_cte) AS ", sql):
        if "_recipe_" in alias:
            continue
        index = int(alias[: -len("_cte")].rpartition("_")[2])
        assert index < RECIPE_SEARCH_ID_START, alias


@dataclass(frozen=True)
class _NodeStandIn:
    """`_cte_alias` reads a node's id and nothing else."""

    node_id: NodeId


def test_nodes_sharing_a_recipe_search_id_get_two_cte_aliases() -> None:
    """Two nodes with one id from the search's space get two CTE aliases.

    They are numbered in the order the conversion reaches them, and neither carries the id; a node numbered outside
    the space keeps upstream's alias.
    """
    visitor = DataflowNodeToSqlCteVisitor.__new__(DataflowNodeToSqlCteVisitor)
    visitor._recipe_search_cte_count = 0
    shared = NodeId(f"jso_{RECIPE_SEARCH_ID_START}")
    first = visitor._cte_alias(_NodeStandIn(shared))  # type: ignore[arg-type]
    second = visitor._cte_alias(_NodeStandIn(shared))  # type: ignore[arg-type]
    assert (first, second) == ("jso_recipe_0_cte", "jso_recipe_1_cte")
    assert visitor._cte_alias(_NodeStandIn(NodeId("sma_10007"))) == "sma_10007_cte"  # type: ignore[arg-type]
