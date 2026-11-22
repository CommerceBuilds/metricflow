"""FORK: validation refuses a derived metric that declares `config.meta.fill_nulls_with` over an input that doesn't fill.

The fork's derived fill is written only in the select that combines metrics' outputs
(`CreateSelectColumnForCombineOutputNode`). Asked for alone, a derived metric reads its inputs' own values, so an
input that doesn't fill would leave NULL in a row the derived metric computes. `DerivedMetricRule` refuses that one
combination (`validations/metrics.py` → `_validate_derived_fill`). The cases extend `fill_manifest/`.
"""

from __future__ import annotations

import logging
import pathlib
import re
import textwrap

import pytest

from metricflow_semantic_interfaces.implementations.semantic_manifest import PydanticSemanticManifest
from metricflow_semantic_interfaces.parsing.dir_to_model import parse_yaml_files_to_validation_ready_semantic_manifest
from metricflow_semantic_interfaces.parsing.objects import YamlConfigFile
from metricflow_semantic_interfaces.validations.metrics import DerivedMetricRule
from metricflow_semantic_interfaces.validations.semantic_manifest_validator import SemanticManifestValidator
from metricflow_semantic_interfaces.validations.validator_helpers import SemanticManifestValidationException

logger = logging.getLogger(__name__)

_FILL_MANIFEST_DIRECTORY = pathlib.Path(__file__).parent / "fill_manifest"


def _validate_with(extra_metric_yaml: str = "") -> None:
    """Runs `DerivedMetricRule` over `fill_manifest/` plus `extra_metric_yaml`; raises on an error."""
    files = [
        YamlConfigFile(filepath=str(path), contents=path.read_text().replace("$source_schema", "fork_fill"))
        for path in sorted(_FILL_MANIFEST_DIRECTORY.glob("*.yaml"))
    ]
    if extra_metric_yaml:
        files.append(YamlConfigFile(filepath="inline_for_test", contents=textwrap.dedent(extra_metric_yaml)))
    manifest = parse_yaml_files_to_validation_ready_semantic_manifest(files).semantic_manifest
    SemanticManifestValidator[PydanticSemanticManifest]([DerivedMetricRule()]).checked_validations(manifest)


def test_a_filled_derived_metric_over_filled_inputs_is_valid() -> None:
    """`total_units` fills, and so do `begin_units` and `end_units`."""
    _validate_with()


def test_a_filled_derived_metric_over_a_filled_derived_input_is_valid() -> None:
    """A derived input that declares its own `config.meta.fill_nulls_with` fills."""
    _validate_with(
        """\
        metric:
          name: total_units_twice
          type: derived
          type_params:
            expr: total_units + begin_units
            metrics:
              - name: total_units
              - name: begin_units
          config:
            meta:
              fill_nulls_with: 0
        """
    )


def test_an_unfilled_derived_metric_over_an_unfilled_input_is_valid() -> None:
    """A derived metric that declares no fill is not this rule's concern."""
    _validate_with(
        """\
        metric:
          name: units_moved
          type: derived
          type_params:
            expr: total_units + received_units
            metrics:
              - name: total_units
              - name: received_units
        """
    )


def test_a_filled_derived_metric_over_an_unfilled_input_is_refused() -> None:
    """`received_units` declares no fill, so a filled derived metric over it is refused, naming the input."""
    with pytest.raises(SemanticManifestValidationException, match=r"\['received_units'\] declare no `fill_nulls_with`"):
        _validate_with(
            """\
            metric:
              name: units_moved_filled
              type: derived
              type_params:
                expr: total_units + received_units
                metrics:
                  - name: total_units
                  - name: received_units
              config:
                meta:
                  fill_nulls_with: 0
            """
        )


def test_a_filled_derived_metric_over_a_ratio_is_refused() -> None:
    """A ratio never fills."""
    with pytest.raises(SemanticManifestValidationException, match=r"\['begin_share'\] declare no `fill_nulls_with`"):
        _validate_with(
            """\
            metric:
              name: begin_share
              type: ratio
              type_params:
                numerator:
                  name: begin_units
                denominator:
                  name: total_units
            ---
            metric:
              name: begin_share_filled
              type: derived
              type_params:
                expr: begin_share * 100
                metrics:
                  - name: begin_share
              config:
                meta:
                  fill_nulls_with: 0
            """
        )


def test_a_filled_derived_metric_over_a_cumulative_input_is_refused() -> None:
    """A cumulative metric never fills in the combine, whatever it declares, so it counts as an input with no fill."""
    with pytest.raises(SemanticManifestValidationException, match=r"\['begin_units_to_date'\] declare no"):
        _validate_with(
            """\
            metric:
              name: begin_units_to_date
              type: cumulative
              type_params:
                measure:
                  name: begin_units
                  fill_nulls_with: 0
                cumulative_type_params:
                  grain_to_date: month
            ---
            metric:
              name: units_to_date_filled
              type: derived
              type_params:
                expr: begin_units_to_date + end_units
                metrics:
                  - name: begin_units_to_date
                  - name: end_units
              config:
                meta:
                  fill_nulls_with: 0
            """
        )


@pytest.mark.parametrize(
    ("fill_yaml", "fill_repr"),
    (("'0'", "'0'"), ("true", "True"), (".inf", "inf"), (".nan", "nan")),
    ids=("text", "bool", "infinity", "not_a_number"),
)
def test_a_derived_fill_that_is_not_a_finite_number_is_refused(fill_yaml: str, fill_repr: str) -> None:
    """The fill is written into the SQL as text, so only a finite `int` or `float` validates."""
    with pytest.raises(
        SemanticManifestValidationException, match=rf"as {re.escape(fill_repr)}, which is not a finite number"
    ):
        _validate_with(
            f"""\
            metric:
              name: total_units_filled_badly
              type: derived
              type_params:
                expr: begin_units + end_units
                metrics:
                  - name: begin_units
                  - name: end_units
              config:
                meta:
                  fill_nulls_with: {fill_yaml}
            """
        )
