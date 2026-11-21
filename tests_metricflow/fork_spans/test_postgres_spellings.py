"""FORK: two Postgres spellings, rendered over the recipe-search tests' manifest with no database.

- A row-level CTE (no GROUP BY, no DISTINCT, no aggregate, in its select or in any sub-query inside it) is written
  `AS NOT MATERIALIZED (`; an aggregating one is written as upstream writes it
  (`PostgresSQLSqlPlanRenderer._cte_materialization_prefix`). A reference to a table or another CTE ends the walk.
- A descending order-by on a metric is `DESC NULLS LAST`; on a dimension it is upstream's `DESC`
  (`PostgresSQLSqlPlanRenderer._render_order_by_direction`, from the order-by spec's own kind).
"""

from __future__ import annotations

import re
from typing import Iterator, Sequence

import pytest
from metricflow_semantics.dag.mf_dag import DagId
from metricflow_semantics.dag.sequential_id import SequentialIdGenerator
from metricflow_semantics.sql.sql_exprs import (
    SqlAggregateFunctionExpression,
    SqlColumnReference,
    SqlColumnReferenceExpression,
    SqlExpressionNode,
    SqlFunction,
)
from metricflow_semantics.sql.sql_join_type import SqlJoinType
from metricflow_semantics.sql.sql_table import SqlTable

from metricflow.dataflow.optimizer.dataflow_optimizer_factory import DataflowPlanOptimization
from metricflow.protocols.sql_client import SqlEngine
from metricflow.sql.optimizer.optimization_levels import SqlOptimizationLevel
from metricflow.sql.render.postgres import PostgresSQLSqlPlanRenderer
from metricflow.sql.render.sql_plan_renderer import DefaultSqlPlanRenderer
from metricflow.sql.sql_cte_node import SqlCteNode
from metricflow.sql.sql_plan import SqlPlanNode, SqlSelectColumn
from metricflow.sql.sql_select_node import SqlJoinDescription, SqlSelectStatementNode
from metricflow.sql.sql_table_node import SqlTableNode
from tests_metricflow.fork_spans.test_recipe_search_ids import _TWO_HOPS, _Engine


@pytest.fixture(scope="module")
def engine() -> Iterator[_Engine]:  # noqa: D103
    with SequentialIdGenerator.id_number_space(10000):
        yield _Engine()


def _sql(
    engine: _Engine,
    metric_names: Sequence[str],
    order_by_names: Sequence[str] = (),
    level: SqlOptimizationLevel = SqlOptimizationLevel.default_level(),
    renderer: DefaultSqlPlanRenderer = PostgresSQLSqlPlanRenderer(),
) -> str:
    with SequentialIdGenerator.id_number_space(0):
        query_spec = engine.query_parser.parse_and_validate_query(
            metric_names=metric_names,
            group_by_names=[_TWO_HOPS],
            order_by_names=list(order_by_names) or None,
            limit=10 if order_by_names else None,
        ).query_spec
        plan = engine.plan_builder().build_plan(
            query_spec, optimizations=DataflowPlanOptimization.enabled_optimizations()
        )
        sql_plan = engine.to_sql.convert_to_sql_plan(
            sql_engine_type=SqlEngine.POSTGRES,
            dataflow_plan_node=plan.sink_node,
            optimization_level=level,
            sql_query_plan_id=DagId.from_str("plan0_optimized"),
        ).sql_plan
        return renderer.render_sql_plan(sql_plan).sql


def test_a_row_level_cte_is_not_materialized_and_an_aggregating_one_is_as_written(engine: _Engine) -> None:
    """A source read shared by two branches is inlined into each; the shared aggregated metric is computed once."""
    sql = _sql(engine, ["txn_share_of_month", "txn_total"])
    written = dict(re.findall(r"(\w+_cte) AS (NOT MATERIALIZED )?\(", sql))
    assert any(alias.startswith("sma_") and keyword for alias, keyword in written.items()), sql
    assert any(alias.startswith("cm_") and not keyword for alias, keyword in written.items()), sql


def _column(table_alias: str) -> SqlExpressionNode:
    return SqlColumnReferenceExpression.create(col_ref=SqlColumnReference(table_alias=table_alias, column_name="x"))


def _select(
    source: SqlPlanNode, aggregate: bool = False, joined: SqlPlanNode | None = None, grouped: bool = False
) -> SqlSelectStatementNode:
    """`SELECT x` (or `SUM(x)`) from `source`, optionally cross-joined to `joined` and grouped by `x`."""
    expr = (
        SqlAggregateFunctionExpression.create(sql_function=SqlFunction.SUM, sql_function_args=[_column("a")])
        if aggregate
        else _column("a")
    )
    return SqlSelectStatementNode.create(
        description="test",
        select_columns=(SqlSelectColumn(expr=expr, column_alias="x"),),
        from_source=source,
        from_source_alias="a",
        join_descs=(
            (SqlJoinDescription(right_source=joined, right_source_alias="b", join_type=SqlJoinType.CROSS_JOIN),)
            if joined is not None
            else ()
        ),
        group_bys=(SqlSelectColumn(expr=_column("a"), column_alias="x"),) if grouped else (),
    )


def _table(name: str) -> SqlTableNode:
    return SqlTableNode.create(sql_table=SqlTable(schema_name="s", table_name=name))


def _prefix(select: SqlSelectStatementNode) -> str:
    return PostgresSQLSqlPlanRenderer()._cte_materialization_prefix(SqlCteNode.create(select, cte_alias="c_cte"))


@pytest.mark.parametrize(
    "select",
    (
        _select(_table("t"), aggregate=True),
        _select(_table("t"), grouped=True),
        _select(_select(_table("t"), aggregate=True)),
        _select(_select(_select(_table("t"), grouped=True))),
        _select(_table("t"), joined=_select(_table("u"), aggregate=True)),
    ),
    ids=("own-aggregate", "own-group-by", "aggregating-from", "grouping-two-levels-down", "aggregating-join"),
)
def test_an_aggregating_cte_never_gets_the_keyword(select: SqlSelectStatementNode) -> None:
    """Inlined at each reference, a CTE with an aggregate anywhere under it would aggregate again for each one."""
    assert _prefix(select) == ""


@pytest.mark.parametrize(
    "select",
    (
        _select(_table("t")),
        _select(_select(_table("t")), joined=_select(_table("u"))),
        _select(_table("aggregating_cte")),
    ),
    ids=("table-read", "row-level-sub-queries", "a-cte-reference-ends-the-walk"),
)
def test_a_row_level_cte_gets_the_keyword(select: SqlSelectStatementNode) -> None:
    """No aggregate under it, down to a table or a CTE reference: each CTE decides for itself."""
    assert _prefix(select) == "NOT MATERIALIZED "


def test_the_default_renderer_writes_no_materialization_keyword(engine: _Engine) -> None:
    """Only Postgres spells it; every other dialect renders as upstream does."""
    sql = _sql(engine, ["txn_share_of_month", "txn_total"], renderer=DefaultSqlPlanRenderer())
    assert "_cte AS (" in sql and "MATERIALIZED" not in sql


@pytest.mark.parametrize("level", (SqlOptimizationLevel.O0, SqlOptimizationLevel.O4, SqlOptimizationLevel.O5))
def test_a_descending_metric_order_is_nulls_last_at_every_level(engine: _Engine, level: SqlOptimizationLevel) -> None:
    """Read from the spec, the kind survives every rewrite: the sub-query reducer's alias and the alias simplifier."""
    sql = _sql(engine, ["txn_total"], ["-txn_total"], level=level)
    assert re.search(r"ORDER BY \S*txn_total DESC NULLS LAST\b", sql), sql


def test_a_descending_dimension_order_and_an_ascending_metric_order_are_upstreams(
    engine: _Engine,
) -> None:
    """A descending dimension order-by and an ascending metric order-by keep upstream's spelling."""
    by_dimension = _sql(engine, ["txn_total"], [f"-{_TWO_HOPS}"])
    assert re.search(rf"ORDER BY \S*{_TWO_HOPS} DESC\n", by_dimension), by_dimension
    ascending = _sql(engine, ["txn_total"], ["txn_total"])
    assert "NULLS" not in ascending and " DESC" not in ascending


def test_the_default_renderer_writes_plain_desc_on_a_metric(engine: _Engine) -> None:  # noqa: D103
    sql = _sql(engine, ["txn_total"], ["-txn_total"], renderer=DefaultSqlPlanRenderer())
    assert "DESC" in sql and "NULLS" not in sql
