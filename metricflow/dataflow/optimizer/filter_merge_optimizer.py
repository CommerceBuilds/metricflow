"""FORK: this module is the CommerceBuilds fork's own (CommerceBuilds/metricflow), not upstream's.

It folds simple-metric branches that read one source and differ only by their metric filters into one read.

The passthrough planner groups simple metrics by their filters' text, and the source-scan optimizer combines only
branches of identical structure, so every distinct metric filter (and every derived metric's input filter) on one
semantic model becomes its own read of that model: its own scan, joins and aggregation. On Postgres those run one
after another, so a request with five filters on one model reads it five times.

This optimizer runs after both. A branch it can fold has exactly this shape, with nothing else in between:

    ComputeMetricsNode                         (every consumer; it computes simple metrics only)
      AggregateSimpleMetricInputsNode          (no filter merge yet; SUM / MIN / MAX / AVERAGE / COUNT_DISTINCT)
        SelectorNode K                         (the branch's inputs and the group-by specs)
          WhereFilterNode W                    (the request's filters and the metric's own)
            SelectorNode P
              JoinOnEntitiesNode X (optional)  (LEFT OUTER joins on an entity only)
                S                              (the source: a ReadSqlSourceNode, under at most a
                                                MetricTimeDimensionTransformNode, JoinToCustomGranularityNodes
                                                and LEFT OUTER JoinOnEntitiesNodes)

Branches whose sources are functionally identical (the same node, or nodes that build the same rows all the way up)
and whose `K` select the same group-by specs are one group. Comparing sources by function, not by object, is what
lets branches over a span read at a grain fold: `DataflowPlanBuilder._span_read_at_grain` keeps one read per span
model and grain, but builds a new metric-time node over it for each branch, so no two such branches share a source
object.

For a group of two or more, the members' filters split into the COMMON ones (on every member) and each member's OWN.
The group becomes one read:

    M  AggregateSimpleMetricInputsNode(filter_merge=members)   AGG(CASE WHEN own_i THEN x END), SUM(CASE WHEN own_i
      |                                                         THEN 1 END) as member i's flag
      WhereFilterNode(common + (own_1 OR own_2 OR ...))         no OR when some member has no own filter
        SelectorNode(union of every P)
          JoinOnEntitiesNode(union of every X's targets)        targets on one entity and node merged into one
            S

and each member's aggregation is replaced by its projection of `M` (`filter_merge=member`), which selects its
columns under their own names and, in a grouped read, keeps only the groups its flag counts a row for. A group the
member's own filters admit no row to is dropped from its projection, exactly as its own branch never produced it, so
the full joins that combine branches return the same members, and a filtered `COUNT DISTINCT` over no rows reads
NULL as before. Ungrouped, every branch is one row and keeps it, as before: a `COUNT DISTINCT` over no rows reads 0.

For SUM, MIN, MAX, AVERAGE and COUNT_DISTINCT, `AGG(CASE WHEN f THEN x END)` equals `AGG(x)` over the rows `f`
admits, since each skips NULLs (COUNT is planned as SUM). The CASE form keeps `M` an aggregating select, so the
Postgres renderer leaves its CTE materialized (`PostgresSQLSqlPlanRenderer`'s row-level check). Every other shape
keeps today's plan: another aggregation, a time-spine join (`JoinToTimeSpineNode` over the aggregate, as
`join_to_timespine` and an offset plan it, or under it), a semi-additive join, a cumulative window
(`JoinOverTimeRangeNode`), a conversion step (its base branch feeds a combine, not a `ComputeMetricsNode`), or any other
node in the branch. A `JoinToCustomGranularityNode` in the source is not a time-spine join of that kind: it adds the
custom grain's column to each row, joining the spine on the row's own day, and drops or adds no row.
"""

from __future__ import annotations

import logging
from collections.abc import Hashable
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

from metricflow_semantics.dag.id_prefix import StaticIdPrefix
from metricflow_semantics.dag.mf_dag import DagId
from metricflow_semantics.semantic_graph.lookups.manifest_object_lookup import ManifestObjectLookup
from metricflow_semantics.specs.instance_spec import LinkableInstanceSpec
from metricflow_semantics.specs.spec_set import InstanceSpecSet
from metricflow_semantics.specs.where_filter.where_filter_spec import WhereFilterSpec
from metricflow_semantics.sql.sql_bind_parameters import SqlBindParameterSet
from metricflow_semantics.sql.sql_join_type import SqlJoinType

from metricflow.dataflow.dataflow_plan import DataflowPlan, DataflowPlanNode
from metricflow.dataflow.nodes.aggregate_simple_metric_inputs import (
    AggregateSimpleMetricInputsNode,
    FilterMerge,
    FilterMergeMember,
)
from metricflow.dataflow.nodes.compute_metrics import ComputeMetricsNode
from metricflow.dataflow.nodes.filter_elements import SelectorNode
from metricflow.dataflow.nodes.join_to_base import JoinDescription, JoinOnEntitiesNode
from metricflow.dataflow.nodes.join_to_custom_granularity import JoinToCustomGranularityNode
from metricflow.dataflow.nodes.metric_time_transform import MetricTimeDimensionTransformNode
from metricflow.dataflow.nodes.read_sql_source import ReadSqlSourceNode
from metricflow.dataflow.nodes.where_filter import WhereFilterNode
from metricflow.dataflow.optimizer.dataflow_plan_optimizer import DataflowPlanOptimizer
from metricflow_semantic_interfaces.type_enums import AggregationType, MetricType

logger = logging.getLogger(__name__)

# Aggregations whose `AGG(CASE WHEN <filter> THEN x END)` equals the member's own branch's aggregate. (COUNT is
# planned as SUM.)
MERGEABLE_AGGREGATIONS = frozenset(
    (
        AggregationType.SUM,
        AggregationType.MIN,
        AggregationType.MAX,
        AggregationType.AVERAGE,
        AggregationType.COUNT_DISTINCT,
    )
)


class _Branch:
    """One foldable branch, its nodes named as in the module docstring."""

    def __init__(  # noqa: D107
        self,
        aggregate: AggregateSimpleMetricInputsNode,
        kept: SelectorNode,
        where: WhereFilterNode,
        pre: SelectorNode,
        join: Optional[JoinOnEntitiesNode],
        source: DataflowPlanNode,
    ) -> None:
        self.aggregate = aggregate
        self.kept = kept
        self.where = where
        self.pre = pre
        self.join = join
        self.source = source
        self.input_names = tuple(spec.element_name for spec in kept.include_specs.simple_metric_input_specs)
        self.group_by_specs: FrozenSet[LinkableInstanceSpec] = frozenset(kept.include_specs.linkable_specs)


def _same_branch(left: DataflowPlanNode, right: DataflowPlanNode) -> bool:
    """Whether two branches produce the same rows: the same node, or functionally identical nodes all the way up."""
    if left is right:
        return True
    if type(left) is not type(right) or len(left.parent_nodes) != len(right.parent_nodes):
        return False
    if not left.functionally_identical(right):
        return False
    if isinstance(left, JoinOnEntitiesNode):
        assert isinstance(right, JoinOnEntitiesNode)
        if len(left.join_targets) != len(right.join_targets):
            return False
        for left_target, right_target in zip(left.join_targets, right.join_targets):
            if left_target.join_on_entity != right_target.join_on_entity:
                return False
            if left_target.join_type is not right_target.join_type:
                return False
    return all(_same_branch(a, b) for a, b in zip(left.parent_nodes, right.parent_nodes))


def _adds_columns_only(join: JoinOnEntitiesNode) -> bool:
    """Whether every join of `join` is a LEFT OUTER join on an entity.

    MetricFlow joins on an entity only where it is unique on the joined side, so such a join adds columns to each row
    and never adds or drops a row.
    """
    return all(
        target.join_type is SqlJoinType.LEFT_OUTER and target.join_on_entity is not None for target in join.join_targets
    )


def _is_plain_source(node: DataflowPlanNode) -> bool:
    """Whether `node` reads a semantic model's rows as they are.

    That is a read, under at most its metric-time node, joins of custom grains and LEFT OUTER joins on entities. Any
    other node (a time-spine join, a cumulative window, a time constraint) keeps today's plan.
    """
    while True:
        if isinstance(node, JoinToCustomGranularityNode):
            node = node.parent_node
        elif isinstance(node, JoinOnEntitiesNode) and _adds_columns_only(node):
            node = node.left_node
        else:
            break
    if isinstance(node, MetricTimeDimensionTransformNode):
        node = node.parent_node
    return isinstance(node, ReadSqlSourceNode)


def _filter_key(spec: WhereFilterSpec) -> Tuple[str, SqlBindParameterSet]:
    return (spec.where_sql, spec.bind_parameters)


class FilterMergeOptimizer(DataflowPlanOptimizer):
    """FORK: @see the module docstring."""

    def __init__(self, manifest_object_lookup: ManifestObjectLookup) -> None:  # noqa: D107
        self._manifest_object_lookup = manifest_object_lookup

    def _as_branch(self, node: DataflowPlanNode, consumers: Sequence[DataflowPlanNode]) -> Optional[_Branch]:
        if not isinstance(node, AggregateSimpleMetricInputsNode) or node.filter_merge is not None:
            return None
        # Only simple metrics computed straight from the aggregate: a time-spine join or an offset reads the aggregate
        # through a `JoinToTimeSpineNode`, a conversion's base branch through a combine, and a cumulative metric is
        # computed by a `ComputeMetricsNode` of its own.
        if not consumers:
            return None
        for consumer in consumers:
            if not isinstance(consumer, ComputeMetricsNode):
                return None
            for metric_spec in consumer.computed_metric_specs:
                if self._manifest_object_lookup.get_metric(metric_spec.element_name).type is not MetricType.SIMPLE:
                    return None
        kept = node.parent_node
        if not isinstance(kept, SelectorNode) or kept.distinct:
            return None
        if len(kept.include_specs.simple_metric_input_specs) == 0:
            return None
        where = kept.parent_node
        if not isinstance(where, WhereFilterNode) or where.always_apply:
            return None
        pre = where.parent_node
        if not isinstance(pre, SelectorNode) or pre.distinct:
            return None
        below = pre.parent_node
        join: Optional[JoinOnEntitiesNode] = None
        if isinstance(below, JoinOnEntitiesNode):
            join = below
            source = below.left_node
            # Every member's rows stay its own under the union of every member's joins only if no join adds or drops a
            # row. Any other join keeps today's plan.
            if not _adds_columns_only(below):
                return None
        else:
            source = below
        if not _is_plain_source(source):
            return None
        for spec in kept.include_specs.simple_metric_input_specs:
            simple_metric_input = self._manifest_object_lookup.simple_metric_name_to_input.get(spec.element_name)
            if simple_metric_input is None or simple_metric_input.agg not in MERGEABLE_AGGREGATIONS:
                return None
        # A member's own filters render inside its aggregate, so they may name only group-by items, never an input.
        for filter_spec in where.filter_specs:
            if filter_spec.instance_spec_set.simple_metric_input_specs:
                return None
        return _Branch(aggregate=node, kept=kept, where=where, pre=pre, join=join, source=source)

    @staticmethod
    def _all_nodes(sink: DataflowPlanNode) -> List[DataflowPlanNode]:
        seen: Dict[int, DataflowPlanNode] = {}
        order: List[DataflowPlanNode] = []
        stack = [sink]
        while stack:
            node = stack.pop()
            if id(node) in seen:
                continue
            seen[id(node)] = node
            order.append(node)
            stack.extend(reversed(node.parent_nodes))
        return order

    @staticmethod
    def _merged_join_targets(branches: Sequence[_Branch]) -> Optional[Tuple[JoinDescription, ...]]:
        """The union of the members' join targets; targets joining one node on one entity become one target."""
        merged: Dict[Hashable, JoinDescription] = {}
        for branch in branches:
            if branch.join is None:
                continue
            for target in branch.join.join_targets:
                if target.join_on_partition_dimensions or target.join_on_partition_time_dimensions:
                    return None
                if target.validity_window is not None:
                    return None
                key = (target.join_on_entity, target.join_type)
                existing = merged.get(key)
                if existing is None:
                    merged[key] = target
                    continue
                if _same_branch(existing.join_node, target.join_node):
                    continue
                if not isinstance(existing.join_node, SelectorNode) or not isinstance(target.join_node, SelectorNode):
                    return None
                if not _same_branch(existing.join_node.parent_node, target.join_node.parent_node):
                    return None
                merged[key] = JoinDescription(
                    join_node=SelectorNode.create(
                        parent_node=existing.join_node.parent_node,
                        include_specs=existing.join_node.include_specs.merge(target.join_node.include_specs).dedupe(),
                    ),
                    join_on_entity=existing.join_on_entity,
                    join_type=existing.join_type,
                    join_on_partition_dimensions=(),
                    join_on_partition_time_dimensions=(),
                    validity_window=None,
                )
        return tuple(merged.values())

    def _merge_group(
        self, branches: Sequence[_Branch], group_index: int
    ) -> Optional[Dict[AggregateSimpleMetricInputsNode, AggregateSimpleMetricInputsNode]]:
        common_keys = set(_filter_key(spec) for spec in branches[0].where.filter_specs)
        for branch in branches[1:]:
            common_keys &= set(_filter_key(spec) for spec in branch.where.filter_specs)
        common = [spec for spec in branches[0].where.filter_specs if _filter_key(spec) in common_keys]
        owns: List[Tuple[WhereFilterSpec, ...]] = [
            tuple(spec for spec in branch.where.filter_specs if _filter_key(spec) not in common_keys)
            for branch in branches
        ]

        filter_specs: List[WhereFilterSpec] = list(common)
        if all(len(own) > 0 for own in owns):
            disjuncts = []
            bind_parameters = SqlBindParameterSet()
            element_set = owns[0][0].element_set
            for own in owns:
                disjuncts.append("(" + " AND ".join(f"({spec.where_sql})" for spec in own) + ")")
                for spec in own:
                    bind_parameters = bind_parameters.merge(spec.bind_parameters)
                    element_set = element_set.union(spec.element_set)
            filter_specs.append(
                WhereFilterSpec(
                    where_sql=" OR ".join(dict.fromkeys(disjuncts)),
                    bind_parameters=bind_parameters,
                    element_set=element_set,
                )
            )

        join_targets = self._merged_join_targets(branches)
        if join_targets is None:
            return None
        source = branches[0].source
        below: DataflowPlanNode = (
            JoinOnEntitiesNode.create(left_node=source, join_targets=join_targets) if join_targets else source
        )
        pre_specs = branches[0].pre.include_specs
        for branch in branches[1:]:
            pre_specs = pre_specs.merge(branch.pre.include_specs)
        pre = SelectorNode.create(parent_node=below, include_specs=pre_specs.dedupe())
        where = WhereFilterNode.create(parent_node=pre, filter_specs=filter_specs)

        group_by_specs = InstanceSpecSet.create_from_specs(branches[0].kept.include_specs.linkable_specs)
        members = tuple(
            FilterMergeMember(
                input_names=branch.input_names,
                filter_specs=own,
                value_names=tuple(f"{name}__fm{group_index}_{i}" for name in branch.input_names),
                # A projection keeps only its own groups; ungrouped, every branch is one row and keeps it.
                has_name=f"fm{group_index}_{i}_has" if own and group_by_specs.linkable_specs else None,
            )
            for i, (branch, own) in enumerate(zip(branches, owns))
        )
        merged_null_fill = branches[0].aggregate.null_fill_value_mapping
        for branch in branches[1:]:
            merged_null_fill = merged_null_fill.merge(branch.aggregate.null_fill_value_mapping)
        merged = AggregateSimpleMetricInputsNode.create(
            parent_node=where,
            null_fill_value_mapping=merged_null_fill,
            filter_merge=FilterMerge(group_by_specs=group_by_specs, members=members),
        )
        return {
            branch.aggregate: AggregateSimpleMetricInputsNode.create(
                parent_node=merged,
                null_fill_value_mapping=branch.aggregate.null_fill_value_mapping,
                filter_merge=FilterMerge(
                    group_by_specs=group_by_specs, member=member, kept_specs=branch.kept.include_specs
                ),
            )
            for branch, member in zip(branches, members)
        }

    def optimize(self, dataflow_plan: DataflowPlan) -> DataflowPlan:  # noqa: D102
        sink = dataflow_plan.sink_node
        # Each group: branches with the same group-by specs over functionally identical sources, in plan order.
        all_nodes = self._all_nodes(sink)
        consumers: Dict[int, List[DataflowPlanNode]] = {}
        for node in all_nodes:
            for parent in node.parent_nodes:
                consumers.setdefault(id(parent), []).append(node)
        groups: List[List[_Branch]] = []
        for node in all_nodes:
            branch = self._as_branch(node, consumers.get(id(node), []))
            if branch is None:
                continue
            for group in groups:
                if group[0].group_by_specs == branch.group_by_specs and _same_branch(group[0].source, branch.source):
                    group.append(branch)
                    break
            else:
                groups.append([branch])

        replacements: Dict[AggregateSimpleMetricInputsNode, AggregateSimpleMetricInputsNode] = {}
        group_index = 0
        for branches in groups:
            if len(branches) < 2:
                continue
            merged = self._merge_group(branches, group_index)
            if merged is None:
                continue
            group_index += 1
            replacements.update(merged)
        if not replacements:
            return dataflow_plan

        rebuilt: Dict[int, DataflowPlanNode] = {}

        def rebuild(node: DataflowPlanNode) -> DataflowPlanNode:
            if id(node) in rebuilt:
                return rebuilt[id(node)]
            if isinstance(node, AggregateSimpleMetricInputsNode) and node in replacements:
                result: DataflowPlanNode = replacements[node]
            else:
                new_parents = [rebuild(parent) for parent in node.parent_nodes]
                if all(new is old for new, old in zip(new_parents, node.parent_nodes)):
                    result = node
                else:
                    result = node.with_new_parents(new_parents)
            rebuilt[id(node)] = result
            return result

        return DataflowPlan(
            plan_id=DagId.from_id_prefix(StaticIdPrefix.OPTIMIZED_DATAFLOW_PLAN_PREFIX),
            sink_nodes=[rebuild(sink)],
        )
