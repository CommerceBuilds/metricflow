# Modified by CommerceBuilds in the fork CommerceBuilds/metricflow; each change is marked `FORK:`.
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from metricflow_semantics.aggregation_properties import AggregationState
from metricflow_semantics.dag.id_prefix import DynamicIdPrefix, StaticIdPrefix
from metricflow_semantics.dag.sequential_id import SequentialIdGenerator
from metricflow_semantics.instances import (
    DimensionInstance,
    EntityInstance,
    InstanceSet,
    SimpleMetricInputInstance,
    TimeDimensionInstance,
)
from metricflow_semantics.model.semantic_manifest_lookup import SemanticManifestLookup
from metricflow_semantics.model.semantics.semantic_model_helper import SemanticModelHelper
from metricflow_semantics.semantic_graph.lookups.simple_metric_model_object_lookup import SimpleMetricModelObjectLookup
from metricflow_semantics.semantic_graph.model_id import SemanticModelId
from metricflow_semantics.specs.column_assoc import ColumnAssociationResolver
from metricflow_semantics.specs.dimension_spec import DimensionSpec
from metricflow_semantics.specs.entity_spec import EntitySpec
from metricflow_semantics.specs.simple_metric_input_spec import SimpleMetricInputSpec
from metricflow_semantics.specs.time_dimension_spec import DEFAULT_TIME_GRANULARITY, TimeDimensionSpec
from metricflow_semantics.sql.sql_exprs import (
    SqlColumnReference,
    SqlColumnReferenceExpression,
    SqlDateTruncExpression,
    SqlExpressionNode,
    SqlExtractExpression,
    SqlStringExpression,
)
from metricflow_semantics.sql.sql_table import SqlTable
from metricflow_semantics.time.granularity import ExpandedTimeGranularity
from metricflow_semantics.time.time_spine_source import TimeSpineSource
from metricflow_semantics.toolkit.mf_logging.lazy_formattable import LazyFormat

from metricflow.dataset.semantic_model_adapter import SemanticModelDataSet
from metricflow.dataset.sql_dataset import SqlDataSet
from metricflow.sql.sql_plan import (
    SqlPlanNode,
    SqlSelectColumn,
)
from metricflow.sql.sql_select_node import SqlSelectStatementNode
from metricflow.sql.sql_select_text_node import SqlSelectTextNode
from metricflow.sql.sql_table_node import SqlTableNode
from metricflow_semantic_interfaces.protocols.dimension import Dimension, DimensionType
from metricflow_semantic_interfaces.protocols.entity import Entity
from metricflow_semantic_interfaces.references import (
    EntityReference,
    SemanticModelElementReference,
    SemanticModelReference,
)
from metricflow_semantic_interfaces.type_enums.date_part import DatePart
from metricflow_semantic_interfaces.type_enums.time_granularity import TimeGranularity

logger = logging.getLogger(__name__)

# FORK: the range every span read is clipped to, as two SQL date expressions (the first and last day, both
# inclusive), set once by the embedding service before the engine is built. A span model is never read without it.
SPAN_RANGE_SQL: Optional[Tuple[str, str]] = None

_IDENTIFIER = re.compile("^[a-zA-Z_][a-zA-Z_0-9]*$")


def span_validity_bounds(validity_dims: Sequence[Dimension]) -> Tuple[str, str]:
    """FORK: the span window's start and end as SQL over the alias `span`."""
    bounds = {}
    for dim in validity_dims:
        assert dim.validity_params is not None
        expr = dim.expr or dim.name
        bounds["start" if dim.validity_params.is_start else "end"] = f"span.{expr}" if _IDENTIFIER.match(expr) else expr
    return bounds["start"], bounds["end"]


def span_periods_sql(
    relation_name: str,
    validity_dims: Sequence[Dimension],
    day_spine: TimeSpineSource,
    period_expr: Optional[str],
    step: Optional[str] = None,
) -> str:
    """FORK: spans read once per period of the requested grain inside the range, not once per day.

    Each row is one span in one period P (P clipped to the range), dated by P's first day, with:
      span_days        the days of P the span covers (a sum over the range weights by it)
      span_is_last     1 when the span covers P's last day (a balance read on the last day)
      span_is_first    1 when the span covers P's first day
      span_group_days  the days of P, from the calendar
    `period_expr` groups the spine's days `d` into periods; None is the whole range as one period.
    """
    if SPAN_RANGE_SQL is None:
        raise RuntimeError(
            "A span model (a semantic model with a validity window and simple-metric inputs) is read only inside a"
            " range: set `convert_semantic_model.SPAN_RANGE_SQL` before the engine is built."
        )
    range_from, range_to = SPAN_RANGE_SQL
    start, end = span_validity_bounds(validity_dims)
    day = day_spine.base_column
    spine = day_spine.sql_table.sql
    weights = (
        f", LEAST({end}, p.p_last + 1) - GREATEST({start}, p.p_first) AS span_days"
        f", CASE WHEN {start} <= p.p_last AND {end} > p.p_last THEN 1 ELSE 0 END AS span_is_last"
        f", CASE WHEN {start} <= p.p_first AND {end} > p.p_first THEN 1 ELSE 0 END AS span_is_first"
        f", p.p_days AS span_group_days"
    )
    in_range = f"WHERE {start} <= {range_to} AND {end} > {range_from} AND {start} < {end}"
    if step:
        # A standard grain: each span is expanded straight to its periods' first days, and joined to the
        # range's periods on that day. No lookup by an expression, so the planner's estimates stay large.
        def trunc(x: str) -> str:
            return f"DATE_TRUNC('{step}', CAST({x} AS TIMESTAMP))"

        return (
            f"WITH span_periods AS ("
            f"SELECT CAST({trunc(f'd.{day}')} AS DATE) AS p_key, MIN(d.{day}) AS p_first, MAX(d.{day}) AS p_last"
            f", COUNT(*) AS p_days FROM {spine} d WHERE d.{day} >= {range_from} AND d.{day} <= {range_to}"
            f" GROUP BY CAST({trunc(f'd.{day}')} AS DATE))"
            f" SELECT span.*, sd.*{weights}"
            f" FROM (SELECT * FROM {relation_name} span {in_range}) span"
            f" CROSS JOIN LATERAL generate_series({trunc(f'GREATEST({start}, {range_from})')}"
            f", {trunc(f'LEAST({end} - 1, {range_to})')}, INTERVAL '1 {step}') AS g(p_start)"
            f" JOIN span_periods p ON p.p_key = CAST(g.p_start AS DATE)"
            f" JOIN {spine} sd ON sd.{day} = p.p_first"
            f" OFFSET 0"
        )
    if period_expr:
        # Every join is an equality: the range's periods are numbered from the spine, each span's first and
        # last period are looked up by day, and the span is expanded to the period numbers between them. An
        # overlap join (`start <= p_last AND end > p_first`) leaves Postgres one plan, a nested loop whose
        # every probe range-scans the spans that started before the period ended.
        return (
            f"WITH span_periods AS ("
            f"SELECT {period_expr} AS p_key, MIN(d.{day}) AS p_first, MAX(d.{day}) AS p_last, COUNT(*) AS p_days"
            f", ROW_NUMBER() OVER (ORDER BY MIN(d.{day})) AS p_no"
            f" FROM {spine} d WHERE d.{day} >= {range_from} AND d.{day} <= {range_to} GROUP BY {period_expr})"
            f", span_day_periods AS ("
            f"SELECT d.{day} AS p_day, p.p_no FROM {spine} d JOIN span_periods p ON p.p_key = {period_expr}"
            f" WHERE d.{day} >= {range_from} AND d.{day} <= {range_to})"
            f" SELECT span.*, sd.*{weights}"
            f" FROM (SELECT * FROM {relation_name} span {in_range}) span"
            f" JOIN span_day_periods lo ON lo.p_day = GREATEST({start}, {range_from})"
            f" JOIN span_day_periods hi ON hi.p_day = LEAST({end} - 1, {range_to})"
            f" CROSS JOIN LATERAL generate_series(lo.p_no, hi.p_no) AS g(p_no)"
            f" JOIN span_periods p ON p.p_no = g.p_no"
            f" JOIN {spine} sd ON sd.{day} = p.p_first"
            # A filter on the read's flags names both the span and its period; pushed in, it turns the joins
            # back into the overlap join. OFFSET 0 keeps every outer filter outside the read.
            f" OFFSET 0"
        )
    return (
        f"SELECT span.*, sd.*"
        f", LEAST({end}, p.p_last + 1) - GREATEST({start}, p.p_first) AS span_days"
        f", CASE WHEN {start} <= p.p_last AND {end} > p.p_last THEN 1 ELSE 0 END AS span_is_last"
        f", CASE WHEN {start} <= p.p_first AND {end} > p.p_first THEN 1 ELSE 0 END AS span_is_first"
        f", p.p_days AS span_group_days"
        f" FROM {relation_name} span"
        f" JOIN (SELECT MIN(d.{day}) AS p_first, MAX(d.{day}) AS p_last, COUNT(*) AS p_days"
        f" FROM {spine} d WHERE d.{day} >= {range_from} AND d.{day} <= {range_to}) p"
        f" ON {start} <= p.p_last AND {end} > p.p_first"
        f" JOIN {spine} sd ON sd.{day} = p.p_first"
        f" WHERE {start} <= {range_to} AND {end} > {range_from}"
    )


@dataclass(frozen=True)
class DimensionConversionResult:
    """Helper class for returning the results of converting dimensions from a semantic model."""

    dimension_instances: Sequence[DimensionInstance]
    time_dimension_instances: Sequence[TimeDimensionInstance]
    select_columns: Sequence[SqlSelectColumn]


class SemanticModelToDataSetConverter:
    """Converts a semantic model in the model to a data set that can be used with the dataflow plan builder.

    Entity links generally refer to the entities used to join the simple-metric source to the dimension source. For
    example, the dimension name "user_id__device_id__platform" has entity links "user_id" and "device_id" and would
    mean that the simple-metric source was joined by "user_id" to an intermediate source, and then it was joined by
    "device_id" to the source containing the "platform" dimension.
    """

    # Regex for inferring whether an expression for an element is a column reference.
    _SQL_IDENTIFIER_REGEX = re.compile("^[a-zA-Z_][a-zA-Z_0-9]*$")

    def __init__(  # noqa: D107
        self,
        column_association_resolver: ColumnAssociationResolver,
        manifest_lookup: SemanticManifestLookup,
    ) -> None:
        self._column_association_resolver = column_association_resolver
        self._manifest_lookup = manifest_lookup
        self._manifest_object_lookup = manifest_lookup.manifest_object_lookup

    def _create_dimension_instance(
        self,
        semantic_model_name: str,
        dimension: Dimension,
        entity_links: Tuple[EntityReference, ...],
    ) -> DimensionInstance:
        """Create a dimension instance from the dimension object in the model."""
        dimension_spec = DimensionSpec(
            element_name=dimension.reference.element_name,
            entity_links=entity_links,
        )
        return DimensionInstance(
            associated_columns=(self._column_association_resolver.resolve_spec(dimension_spec),),
            spec=dimension_spec,
            defined_from=(
                SemanticModelElementReference(
                    semantic_model_name=semantic_model_name,
                    element_name=dimension.reference.element_name,
                ),
            ),
        )

    def _create_time_dimension_instance(
        self,
        element_name: str,
        entity_links: Tuple[EntityReference, ...],
        time_granularity: Optional[ExpandedTimeGranularity] = None,
        date_part: Optional[DatePart] = None,
        semantic_model_name: Optional[str] = None,
    ) -> TimeDimensionInstance:
        """Create a time dimension instance from the dimension object from a semantic model in the model."""
        time_dimension_spec = TimeDimensionSpec(
            element_name=element_name,
            entity_links=entity_links,
            time_granularity=time_granularity,
            date_part=date_part,
        )

        return TimeDimensionInstance(
            associated_columns=(self._column_association_resolver.resolve_spec(time_dimension_spec),),
            spec=time_dimension_spec,
            defined_from=(
                (
                    SemanticModelElementReference(
                        semantic_model_name=semantic_model_name,
                        element_name=element_name,
                    ),
                )
                if semantic_model_name
                else ()
            ),
        )

    def _create_entity_instance(
        self,
        semantic_model_name: str,
        entity: Entity,
        entity_links: Tuple[EntityReference, ...],
    ) -> EntityInstance:
        """Create an entity instance from the entity object from a semantic modelin the model."""
        entity_spec = EntitySpec(
            element_name=entity.reference.element_name,
            entity_links=entity_links,
        )
        return EntityInstance(
            associated_columns=(self._column_association_resolver.resolve_spec(entity_spec),),
            spec=entity_spec,
            defined_from=(
                SemanticModelElementReference(
                    semantic_model_name=semantic_model_name,
                    element_name=entity.reference.element_name,
                ),
            ),
        )

    @staticmethod
    def _make_element_sql_expr(
        table_alias: str, element_name: str, element_expr: Optional[str] = None
    ) -> SqlExpressionNode:
        """Create an expression that can be used for reading the element from the semantic model's SQL."""
        if element_expr:
            if SemanticModelToDataSetConverter._SQL_IDENTIFIER_REGEX.match(
                element_expr
            ) and element_expr.upper() not in (
                "TRUE",
                "FALSE",
                "NULL",
            ):
                return SqlColumnReferenceExpression.create(
                    SqlColumnReference(
                        table_alias=table_alias,
                        column_name=element_expr,
                    )
                )
            return SqlStringExpression.create(sql_expr=element_expr)

        return SqlColumnReferenceExpression.create(
            SqlColumnReference(
                table_alias=table_alias,
                column_name=element_name,
            )
        )

    def _convert_simple_metric_inputs(
        self,
        model_lookup: SimpleMetricModelObjectLookup,
        table_alias: str,
    ) -> Tuple[Sequence[SimpleMetricInputInstance], Sequence[SqlSelectColumn]]:
        # Convert the simple metrics associated with the given model.
        simple_metric_instances = []
        select_columns = []
        for (
            aggregation_configuration,
            simple_metric_inputs,
        ) in model_lookup.aggregation_configuration_to_simple_metric_inputs.items():
            for simple_metric_input in simple_metric_inputs:
                spec = SimpleMetricInputSpec(
                    element_name=simple_metric_input.name,
                    fill_nulls_with=None,
                )
                instance = SimpleMetricInputInstance(
                    associated_columns=(self._column_association_resolver.resolve_spec(spec),),
                    spec=spec,
                    defined_from=(
                        SemanticModelElementReference(
                            semantic_model_name=model_lookup.model_id.model_name,
                            element_name=simple_metric_input.name,
                        ),
                    ),
                    aggregation_state=AggregationState.NON_AGGREGATED,
                )
                simple_metric_instances.append(instance)
                select_columns.append(
                    SqlSelectColumn(
                        expr=SemanticModelToDataSetConverter._make_element_sql_expr(
                            table_alias=table_alias,
                            element_name=simple_metric_input.name,
                            element_expr=simple_metric_input.expr,
                        ),
                        column_alias=instance.associated_column.column_name,
                    )
                )

        return simple_metric_instances, select_columns

    def _convert_dimensions(
        self,
        semantic_model_name: str,
        dimensions: Sequence[Dimension],
        entity_links: Tuple[EntityReference, ...],
        table_alias: str,
    ) -> DimensionConversionResult:
        dimension_instances = []
        time_dimension_instances = []
        select_columns = []

        for dimension in dimensions or []:
            dimension_select_expr = SemanticModelToDataSetConverter._make_element_sql_expr(
                table_alias=table_alias,
                element_name=dimension.reference.element_name,
                element_expr=dimension.expr,
            )
            if dimension.type == DimensionType.CATEGORICAL:
                dimension_instance = self._create_dimension_instance(
                    semantic_model_name=semantic_model_name,
                    dimension=dimension,
                    entity_links=entity_links,
                )
                dimension_instances.append(dimension_instance)
                select_columns.append(
                    SqlSelectColumn(
                        expr=dimension_select_expr,
                        column_alias=dimension_instance.associated_column.column_name,
                    )
                )
            elif dimension.type == DimensionType.TIME:
                derived_time_dimension_instances, time_select_columns = self._convert_time_dimension(
                    dimension_select_expr=dimension_select_expr,
                    dimension=dimension,
                    semantic_model_name=semantic_model_name,
                    entity_links=entity_links,
                )
                time_dimension_instances += derived_time_dimension_instances
                select_columns += time_select_columns
            else:
                assert False, f"Unhandled dimension type: {dimension.type}"

        return DimensionConversionResult(
            dimension_instances=dimension_instances,
            time_dimension_instances=time_dimension_instances,
            select_columns=select_columns,
        )

    def _convert_time_dimension(
        self,
        dimension_select_expr: SqlExpressionNode,
        dimension: Dimension,
        semantic_model_name: str,
        entity_links: Tuple[EntityReference, ...],
    ) -> Tuple[List[TimeDimensionInstance], List[SqlSelectColumn]]:
        """Converts Dimension objects with type TIME into the relevant DataSet columns.

        Time dimensions require special handling that includes adding additional instances
        and select column statements for each granularity and date part
        """
        time_dimension_instances: List[TimeDimensionInstance] = []
        select_columns: List[SqlSelectColumn] = []

        defined_time_granularity = DEFAULT_TIME_GRANULARITY
        if dimension.type_params and dimension.type_params.time_granularity:
            defined_time_granularity = dimension.type_params.time_granularity

        time_dimension_instance = self._create_time_dimension_instance(
            semantic_model_name=semantic_model_name,
            element_name=dimension.reference.element_name,
            entity_links=entity_links,
            time_granularity=ExpandedTimeGranularity.from_time_granularity(defined_time_granularity),
        )
        time_dimension_instances.append(time_dimension_instance)

        # Until we support minimal granularities, we cannot truncate for
        # any time dimension used as part of a validity window, since a validity window might
        # be stored in seconds while we would truncate to daily.
        if dimension.validity_params:
            select_columns.append(
                SqlSelectColumn(
                    expr=dimension_select_expr,
                    column_alias=time_dimension_instance.associated_column.column_name,
                )
            )
        else:
            select_columns.append(
                self._build_column_for_standard_time_granularity(
                    time_granularity=defined_time_granularity,
                    expr=dimension_select_expr,
                    column_alias=time_dimension_instance.associated_column.column_name,
                )
            )

        new_instances, new_columns = self._build_time_dimension_instances_and_columns(
            semantic_model_name=semantic_model_name,
            defined_time_granularity=defined_time_granularity,
            element_name=dimension.reference.element_name,
            entity_links=entity_links,
            dimension_select_expr=dimension_select_expr,
        )
        time_dimension_instances.extend(new_instances)
        select_columns.extend(new_columns)
        return (time_dimension_instances, select_columns)

    def _build_time_dimension_instances_and_columns(
        self,
        defined_time_granularity: TimeGranularity,
        element_name: str,
        entity_links: Tuple[EntityReference, ...],
        dimension_select_expr: SqlExpressionNode,
        semantic_model_name: Optional[str] = None,
    ) -> Tuple[List[TimeDimensionInstance], List[SqlSelectColumn]]:
        time_dimension_instances: List[TimeDimensionInstance] = []
        select_columns: List[SqlSelectColumn] = []
        # Add time dimensions with a larger granularity for ease in query resolution
        for time_granularity in TimeGranularity:
            if time_granularity.to_int() > defined_time_granularity.to_int():
                time_dimension_instance = self._create_time_dimension_instance(
                    semantic_model_name=semantic_model_name,
                    element_name=element_name,
                    entity_links=entity_links,
                    time_granularity=ExpandedTimeGranularity.from_time_granularity(time_granularity),
                )
                time_dimension_instances.append(time_dimension_instance)

                select_columns.append(
                    self._build_column_for_standard_time_granularity(
                        time_granularity=time_granularity,
                        expr=dimension_select_expr,
                        column_alias=time_dimension_instance.associated_column.column_name,
                    )
                )

        # Add all date part options for easy query resolution
        for date_part in DatePart:
            if date_part.to_int() >= defined_time_granularity.to_int():
                time_dimension_instance = self._create_time_dimension_instance(
                    semantic_model_name=semantic_model_name,
                    element_name=element_name,
                    entity_links=entity_links,
                    date_part=date_part,
                )
                time_dimension_instances.append(time_dimension_instance)

                select_columns.append(
                    SqlSelectColumn(
                        expr=SqlExtractExpression.create(date_part=date_part, arg=dimension_select_expr),
                        column_alias=time_dimension_instance.associated_column.column_name,
                    )
                )

        return (time_dimension_instances, select_columns)

    def _build_column_for_standard_time_granularity(
        self, time_granularity: TimeGranularity, expr: SqlExpressionNode, column_alias: str
    ) -> SqlSelectColumn:
        return SqlSelectColumn(
            expr=SqlDateTruncExpression.create(time_granularity=time_granularity, arg=expr), column_alias=column_alias
        )

    def _create_entity_instances(
        self,
        semantic_model_name: str,
        entities: Sequence[Entity],
        entity_links: Tuple[EntityReference, ...],
        table_alias: str,
    ) -> Tuple[Sequence[EntityInstance], Sequence[SqlSelectColumn]]:
        entity_instances = []
        select_columns = []
        for entity in entities or []:
            # We don't want to create something like user_id__user_id, so skip if the link is the same as the
            # entity.
            if len(entity_links) == 1 and entity.reference == entity_links[0]:
                continue

            entity_instance = self._create_entity_instance(
                semantic_model_name=semantic_model_name,
                entity=entity,
                entity_links=entity_links,
            )

            entity_instances.append(entity_instance)
            select_columns.append(
                SqlSelectColumn(
                    expr=SemanticModelToDataSetConverter._make_element_sql_expr(
                        table_alias=table_alias,
                        element_name=entity.reference.element_name,
                        element_expr=entity.expr,
                    ),
                    column_alias=entity_instance.associated_column.column_name,
                )
            )
        return entity_instances, select_columns

    def create_sql_source_data_set(self, model_reference: SemanticModelReference) -> SemanticModelDataSet:
        """Create an SQL source data set from a semantic model in the model."""
        # Gather all instances and columns from all semantic models.
        all_simple_metric_input_instances: List[SimpleMetricInputInstance] = []
        all_dimension_instances: List[DimensionInstance] = []
        all_time_dimension_instances: List[TimeDimensionInstance] = []
        all_entity_instances: List[EntityInstance] = []

        all_select_columns: List[SqlSelectColumn] = []
        model_name = model_reference.semantic_model_name
        from_source_alias = SequentialIdGenerator.create_next_id(DynamicIdPrefix(prefix=f"{model_name}_src")).str_value
        # Handle simple metrics
        model_lookup = self._manifest_object_lookup.model_id_to_simple_metric_model_lookup.get(
            SemanticModelId.get_instance(model_reference.semantic_model_name)
        )

        if model_lookup is not None:
            simple_metric_input_instances, select_columns = self._convert_simple_metric_inputs(
                model_lookup=model_lookup,
                table_alias=from_source_alias,
            )
            all_simple_metric_input_instances.extend(simple_metric_input_instances)
            all_select_columns.extend(select_columns)

        # Group by items in the semantic model can be accessed though a subset of the entities defined in the model.
        possible_entity_links: List[Tuple[EntityReference, ...]] = [
            (),
        ]

        semantic_model = self._manifest_lookup.semantic_model_lookup.get_by_reference(model_reference)
        if semantic_model is None:
            raise RuntimeError(
                LazyFormat("Did not find a semantic model with the given reference", model_reference=model_reference)
            )
        for entity_link in SemanticModelHelper.entity_links_for_local_elements(semantic_model):
            possible_entity_links.append((entity_link,))

        # Handle dimensions
        conversion_results = [
            self._convert_dimensions(
                semantic_model_name=semantic_model.name,
                dimensions=semantic_model.dimensions,
                entity_links=entity_links,
                table_alias=from_source_alias,
            )
            for entity_links in possible_entity_links
        ]

        all_dimension_instances.extend(
            [
                dimension_instance
                for conversion_result in conversion_results
                for dimension_instance in conversion_result.dimension_instances
            ]
        )

        all_time_dimension_instances.extend(
            [
                time_dimension_instance
                for conversion_result in conversion_results
                for time_dimension_instance in conversion_result.time_dimension_instances
            ]
        )

        all_select_columns.extend(
            [
                select_column
                for conversion_result in conversion_results
                for select_column in conversion_result.select_columns
            ]
        )

        # Handle entities
        for entity_links in possible_entity_links:
            entity_instances, select_columns = self._create_entity_instances(
                semantic_model_name=semantic_model.name,
                entities=semantic_model.entities,
                entity_links=entity_links,
                table_alias=from_source_alias,
            )
            all_entity_instances.extend(entity_instances)
            all_select_columns.extend(select_columns)

        # Generate the "from" clause depending on whether it's an SQL query or an SQL table.
        from_source: SqlPlanNode = SqlTableNode.create(
            sql_table=SqlTable.from_string(semantic_model.node_relation.relation_name)
        )
        # FORK: a semantic model with a validity window AND simple-metric inputs holds spans. It is read once per
        # period inside the range, here the whole range as one period (`span_periods_sql`); grouped by a grain, the
        # plan builder swaps in the read at that grain (`DataflowPlanBuilder._span_read_at_grain`).
        validity_dims = [dim for dim in semantic_model.dimensions if dim.validity_params is not None]
        if validity_dims and model_lookup is not None:
            day_spine = TimeSpineSource.build_standard_time_spine_sources(self._manifest_lookup.semantic_manifest)[
                TimeGranularity.DAY
            ]
            from_source = SqlSelectTextNode.create(
                span_periods_sql(semantic_model.node_relation.relation_name, validity_dims, day_spine, None)
            )

        select_statement_node = SqlSelectStatementNode.create(
            description=f"Read Elements From Semantic Model '{semantic_model.name}'",
            select_columns=tuple(all_select_columns),
            from_source=from_source,
            from_source_alias=from_source_alias,
        )

        return SemanticModelDataSet(
            semantic_model_reference=SemanticModelReference(semantic_model_name=semantic_model.name),
            instance_set=InstanceSet(
                simple_metric_input_instances=tuple(all_simple_metric_input_instances),
                dimension_instances=tuple(all_dimension_instances),
                time_dimension_instances=tuple(all_time_dimension_instances),
                entity_instances=tuple(all_entity_instances),
                metric_instances=(),
            ),
            sql_select_node=select_statement_node,
        )

    def build_time_spine_source_data_set(self, time_spine_source: TimeSpineSource) -> SqlDataSet:
        """Build data set for time spine."""
        from_source_alias = SequentialIdGenerator.create_next_id(StaticIdPrefix.TIME_SPINE_SOURCE).str_value
        base_granularity = time_spine_source.base_granularity
        base_column_name = time_spine_source.base_column

        time_dimension_instances: List[TimeDimensionInstance] = []
        select_columns: List[SqlSelectColumn] = []

        # Build base time dimension instances & columns
        base_time_dimension_instance = self._create_time_dimension_instance(
            element_name=base_column_name,
            entity_links=(),
            time_granularity=ExpandedTimeGranularity.from_time_granularity(base_granularity),
        )
        time_dimension_instances.append(base_time_dimension_instance)
        base_dimension_select_expr = SqlColumnReferenceExpression.from_column_reference(
            table_alias=from_source_alias, column_name=base_column_name
        )
        base_select_column = SqlSelectColumn(
            expr=base_dimension_select_expr, column_alias=base_time_dimension_instance.associated_column.column_name
        )
        select_columns.append(base_select_column)
        new_base_instances, new_base_columns = self._build_time_dimension_instances_and_columns(
            defined_time_granularity=base_granularity,
            element_name=base_column_name,
            entity_links=(),
            dimension_select_expr=base_dimension_select_expr,
        )
        time_dimension_instances.extend(new_base_instances)
        select_columns.extend(new_base_columns)

        # Build custom granularity time dimension instances & columns
        for custom_granularity in time_spine_source.custom_granularities:
            custom_time_dimension_instance = self._create_time_dimension_instance(
                # Use base column name here for ease in building metric_time elements in MetricTimeDimensionTransformNode.
                element_name=base_column_name,
                entity_links=(),
                time_granularity=ExpandedTimeGranularity(
                    name=custom_granularity.name, base_granularity=base_granularity
                ),
            )
            time_dimension_instances.append(custom_time_dimension_instance)
            custom_select_column = SqlSelectColumn(
                expr=SemanticModelToDataSetConverter._make_element_sql_expr(
                    table_alias=from_source_alias, element_name=custom_granularity.parsed_column_name
                ),
                column_alias=custom_time_dimension_instance.associated_column.column_name,
            )
            select_columns.append(custom_select_column)

        return SqlDataSet(
            instance_set=InstanceSet(time_dimension_instances=tuple(time_dimension_instances)),
            sql_select_node=SqlSelectStatementNode.create(
                description=time_spine_source.data_set_description,
                select_columns=tuple(select_columns),
                from_source=SqlTableNode.create(sql_table=time_spine_source.sql_table),
                from_source_alias=from_source_alias,
            ),
        )
