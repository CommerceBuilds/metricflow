# Modified by CommerceBuilds in the fork CommerceBuilds/metricflow; each change is marked `FORK:`.
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Optional, Sequence, Tuple  # FORK: `Optional` and `Tuple`, for `FilterMerge`

from metricflow_semantics.dag.id_prefix import IdPrefix, StaticIdPrefix
from metricflow_semantics.dag.mf_dag import DisplayedProperty
from metricflow_semantics.specs.spec_set import InstanceSpecSet  # FORK: for `FilterMerge`
from metricflow_semantics.specs.where_filter.where_filter_spec import WhereFilterSpec  # FORK: for `FilterMerge`
from metricflow_semantics.toolkit.visitor import VisitorOutputT
from typing_extensions import override

from metricflow.dataflow.builder.aggregation_helper import NullFillValueMapping
from metricflow.dataflow.dataflow_plan import DataflowPlanNode
from metricflow.dataflow.dataflow_plan_visitor import DataflowPlanNodeVisitor


@dataclass(frozen=True)
class FilterMergeMember:
    """FORK: one simple-metric input in a filter-merged read (`FilterMergeOptimizer`).

    Attributes:
        input_names: the simple-metric inputs its branch aggregates (passthrough gives one branch every simple
            metric of one model under one filter text).
        filter_specs: the member's own metric filters (empty when it has none); the read's common filters are
            applied to every row, these only inside the member's aggregate.
        value_names: per input, the input-spec name of its aggregated column in the merged read.
        has_name: the input-spec name of the member's flag column, the count of rows its filters admit; only for a
            member with its own filters in a grouped read, the one case whose projection must drop groups.
    """

    input_names: Tuple[str, ...]
    filter_specs: Tuple[WhereFilterSpec, ...]
    value_names: Tuple[str, ...]
    has_name: Optional[str]


@dataclass(frozen=True)
class FilterMerge:
    """FORK: what a filter-merged `AggregateSimpleMetricInputsNode` does instead of a plain aggregation.

    `members` set: the MERGED read. It aggregates each member over its parent's rows grouped by `group_by_specs`,
    each as `AGG(CASE WHEN <the member's filters> THEN expr END)`, beside the member's flag where it has one.
    `member` set: one member's PROJECTION of its parent, a merged read. It selects that member's column under the
    input's own name and keeps only the groups its flag counts rows for, so it returns exactly the rows the member's
    own branch returns unmerged. `kept_specs` is the specs that branch's aggregation read.
    """

    group_by_specs: InstanceSpecSet
    members: Tuple[FilterMergeMember, ...] = ()
    member: Optional[FilterMergeMember] = None
    kept_specs: Optional[InstanceSpecSet] = None


@dataclass(frozen=True, eq=False)
class AggregateSimpleMetricInputsNode(DataflowPlanNode):
    """A node that aggregates the simple-metric inputs by the associated group-by elements.

    The output instances of this node contain context on the appropriate null-fill value. The `ComputeMetricsNode` uses
    this context to render the appropriate `COALESCE` expressions.

    # TODO: Verify `COALESCE` is rendered in `ComputeMetricsNode` to handle `WHERE` filter behavior.
    """

    # The `null_fill_value_mapping` should contain an entry for each simple-metric input to support
    # `ComputeMetricsBranchCombiner`.
    null_fill_value_mapping: NullFillValueMapping
    # FORK: set only by `FilterMergeOptimizer`. @see `FilterMerge`.
    filter_merge: Optional[FilterMerge] = None

    def __post_init__(self) -> None:  # noqa: D105
        super().__post_init__()
        assert len(self.parent_nodes) == 1

    @staticmethod
    def create(  # noqa: D102
        parent_node: DataflowPlanNode,
        null_fill_value_mapping: NullFillValueMapping,
        filter_merge: Optional[FilterMerge] = None,  # FORK: @see `FilterMerge`
    ) -> AggregateSimpleMetricInputsNode:
        return AggregateSimpleMetricInputsNode(
            parent_nodes=(parent_node,),
            null_fill_value_mapping=null_fill_value_mapping,
            filter_merge=filter_merge,  # FORK: @see `FilterMerge`
        )

    @classmethod
    def id_prefix(cls) -> IdPrefix:  # noqa: D102
        return StaticIdPrefix.DATAFLOW_NODE_AGGREGATE_ID_PREFIX

    def accept(self, visitor: DataflowPlanNodeVisitor[VisitorOutputT]) -> VisitorOutputT:  # noqa: D102
        return visitor.visit_aggregate_simple_metric_inputs_node(self)

    @property
    def description(self) -> str:  # noqa: D102
        return """Aggregate Inputs for Simple Metrics"""

    @property
    def parent_node(self) -> DataflowPlanNode:  # noqa: D102
        return self.parent_nodes[0]

    def functionally_identical(self, other_node: DataflowPlanNode) -> bool:  # noqa: D102
        return (
            isinstance(other_node, self.__class__)
            and self.null_fill_value_mapping == other_node.null_fill_value_mapping
            and self.filter_merge == other_node.filter_merge  # FORK: @see `FilterMerge`
        )

    def with_new_parents(  # noqa: D102
        self, new_parent_nodes: Sequence[DataflowPlanNode]
    ) -> AggregateSimpleMetricInputsNode:
        assert len(new_parent_nodes) == 1
        return AggregateSimpleMetricInputsNode(
            parent_nodes=tuple(new_parent_nodes),
            null_fill_value_mapping=self.null_fill_value_mapping,
            filter_merge=self.filter_merge,  # FORK: @see `FilterMerge`
        )

    @cached_property
    @override
    def displayed_properties(self) -> Sequence[DisplayedProperty]:
        properties: list[DisplayedProperty] = list(super().displayed_properties)
        properties.append(
            DisplayedProperty("null_fill_value_mapping", self.null_fill_value_mapping.element_name_to_null_fill_value)
        )
        if self.filter_merge is not None:  # FORK: @see `FilterMerge`
            properties.append(DisplayedProperty("filter_merge", self.filter_merge))
        return properties
