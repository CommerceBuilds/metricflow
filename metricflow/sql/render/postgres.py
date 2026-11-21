# Modified by CommerceBuilds in the fork CommerceBuilds/metricflow; each change is marked `FORK:`.
from __future__ import annotations

from typing import Collection

from metricflow_semantics.errors.error_classes import UnsupportedEngineFeatureError
from metricflow_semantics.sql.sql_bind_parameters import SqlBindParameterSet
from metricflow_semantics.sql.sql_exprs import (
    SqlAddTimeExpression,
    SqlAggregateFunctionExpression,
    SqlArithmeticExpression,
    SqlArithmeticOperator,
    SqlExpressionNode,
    SqlFunction,
    SqlGenerateUuidExpression,
    SqlIntegerExpression,
    SqlPercentileExpression,
    SqlPercentileFunctionType,
    SqlSubtractTimeIntervalExpression,
)
from typing_extensions import override

from metricflow.protocols.sql_client import SqlEngine
from metricflow.sql.render.expr_renderer import (
    DefaultSqlExpressionRenderer,
    SqlExpressionRenderer,
    SqlExpressionRenderResult,
)
from metricflow.sql.render.sql_plan_renderer import DefaultSqlPlanRenderer
from metricflow.sql.sql_cte_node import SqlCteNode
from metricflow.sql.sql_select_node import SqlOrderByDescription, SqlSelectStatementNode
from metricflow_semantic_interfaces.enum_extension import assert_values_exhausted
from metricflow_semantic_interfaces.type_enums.time_granularity import TimeGranularity


class PostgresSqlExpressionRenderer(DefaultSqlExpressionRenderer):
    """Expression renderer for the PostgreSQL engine."""

    sql_engine = SqlEngine.POSTGRES

    @property
    @override
    def double_data_type(self) -> str:
        """Custom double data type for the PostgreSQL engine."""
        return "DOUBLE PRECISION"

    @property
    @override
    def supported_percentile_function_types(self) -> Collection[SqlPercentileFunctionType]:
        return {SqlPercentileFunctionType.CONTINUOUS, SqlPercentileFunctionType.DISCRETE}

    @override
    def visit_subtract_time_interval_expr(self, node: SqlSubtractTimeIntervalExpression) -> SqlExpressionRenderResult:
        """Render time delta operations for PostgreSQL, which needs custom support for quarterly granularity."""
        arg_rendered = node.arg.accept(self)

        count = node.count
        granularity = node.granularity
        if granularity is TimeGranularity.QUARTER:
            granularity = TimeGranularity.MONTH
            count *= 3
        return SqlExpressionRenderResult(
            sql=f"{arg_rendered.sql} - MAKE_INTERVAL({granularity.value}s => {count})",
            bind_parameter_set=arg_rendered.bind_parameter_set,
        )

    @override
    def visit_add_time_expr(self, node: SqlAddTimeExpression) -> SqlExpressionRenderResult:
        """Render time delta operations for PostgreSQL, which needs custom support for quarterly granularity."""
        granularity = node.granularity
        count_expr = node.count_expr
        if granularity is TimeGranularity.QUARTER:
            granularity = TimeGranularity.MONTH
            SqlArithmeticExpression.create(
                left_expr=node.count_expr,
                operator=SqlArithmeticOperator.MULTIPLY,
                right_expr=SqlIntegerExpression.create(3),
            )

        arg_rendered = node.arg.accept(self)
        count_rendered = count_expr.accept(self)
        count_sql = f"({count_rendered.sql})" if count_expr.requires_parenthesis else count_rendered.sql

        return SqlExpressionRenderResult(
            sql=f"{arg_rendered.sql} + MAKE_INTERVAL({granularity.value}s => CAST ({count_sql} AS INTEGER))",
            bind_parameter_set=SqlBindParameterSet.merge_iterable(
                (arg_rendered.bind_parameter_set, count_rendered.bind_parameter_set)
            ),
        )

    @override
    def visit_generate_uuid_expr(self, node: SqlGenerateUuidExpression) -> SqlExpressionRenderResult:
        return SqlExpressionRenderResult(
            sql="GEN_RANDOM_UUID()",
            bind_parameter_set=SqlBindParameterSet(),
        )

    @override
    def visit_percentile_expr(self, node: SqlPercentileExpression) -> SqlExpressionRenderResult:
        """Render a percentile expression for Postgres."""
        arg_rendered = self.render_sql_expr(node.order_by_arg)
        params = arg_rendered.bind_parameter_set
        percentile = node.percentile_args.percentile

        if node.percentile_args.function_type is SqlPercentileFunctionType.CONTINUOUS:
            function_str = "PERCENTILE_CONT"
        elif node.percentile_args.function_type is SqlPercentileFunctionType.DISCRETE:
            function_str = "PERCENTILE_DISC"
        elif node.percentile_args.function_type is SqlPercentileFunctionType.APPROXIMATE_CONTINUOUS:
            raise UnsupportedEngineFeatureError(
                "Approximate continuous percentile aggregate not supported for Postgres. Set "
                + "use_approximate_percentile to false in all percentile simple-metrics."
            )
        elif node.percentile_args.function_type is SqlPercentileFunctionType.APPROXIMATE_DISCRETE:
            raise UnsupportedEngineFeatureError(
                "Approximate discrete percentile aggregate not supported for Postgres. Set "
                + "use_approximate_percentile to false in all percentile simple-metrics."
            )
        else:
            assert_values_exhausted(node.percentile_args.function_type)

        return SqlExpressionRenderResult(
            sql=f"{function_str}({percentile}) WITHIN GROUP (ORDER BY ({arg_rendered.sql}))",
            bind_parameter_set=params,
        )


class PostgresSQLSqlPlanRenderer(DefaultSqlPlanRenderer):
    """Plan renderer for the PostgreSQL engine."""

    EXPR_RENDERER = PostgresSqlExpressionRenderer()

    @property
    @override
    def expr_renderer(self) -> SqlExpressionRenderer:
        return self.EXPR_RENDERER

    @override
    def _cte_materialization_prefix(self, node: SqlCteNode) -> str:
        """FORK: a row-level CTE (no GROUP BY, DISTINCT or aggregate, in it or a sub-query) is `NOT MATERIALIZED`.

        Postgres materializes a CTE referenced more than once, so no filter of any reference reaches the table under
        it: a source read shared by two branches is read whole. Not materialized, the CTE is inlined into each
        reference, which gets its own filters and indexes. An aggregating CTE is written as upstream writes it:
        materialized once, it holds the small aggregated rows every reference shares. Either way the rows are the same.
        """
        select = node.select_statement
        if not isinstance(select, SqlSelectStatementNode) or _aggregates(select):
            return ""
        return "NOT MATERIALIZED "

    @override
    def _render_order_by_direction(self, order_by: SqlOrderByDescription) -> str:
        """FORK: a descending order-by on a metric is `DESC NULLS LAST`.

        Postgres sorts NULLs as larger than every value, so a plain `DESC` puts a metric's NULLs first, and a ranking
        with a limit fills its top rows with members that have no value. Ascending already puts NULLs last, so the two
        directions then agree. A dimension's order-by is written as upstream writes it.
        """
        if order_by.desc and order_by.is_metric:
            return " DESC NULLS LAST"
        return super()._render_order_by_direction(order_by)


def _aggregates(select: SqlSelectStatementNode) -> bool:
    """FORK: whether a select, or any sub-query inside it, groups, deduplicates or aggregates.

    A CTE whose own select only computes over an aggregating sub-query (a `Compute Metrics` over `Aggregate Inputs`)
    aggregates too: inlined at each reference, it would aggregate the table under it again for each one. The walk
    follows the sub-queries in the select's FROM and JOINs; a table or a CTE reference ends it, since each CTE decides
    for itself (@see `_cte_materialization_prefix`).
    """
    if (
        len(select.group_bys) > 0
        or select.distinct
        or any(_has_aggregate(column.expr) for column in select.select_columns)
    ):
        return True
    sources = [select.from_source] + [join_desc.right_source for join_desc in select.join_descs]
    return any(isinstance(source, SqlSelectStatementNode) and _aggregates(source) for source in sources)


def _has_aggregate(expr: SqlExpressionNode) -> bool:
    """FORK: whether an expression is, or contains, an aggregate function. A COALESCE is not one."""
    if isinstance(expr, SqlPercentileExpression):
        return True
    if isinstance(expr, SqlAggregateFunctionExpression) and SqlFunction.is_aggregation(expr.sql_function):
        return True
    return any(_has_aggregate(parent) for parent in expr.parent_nodes)
