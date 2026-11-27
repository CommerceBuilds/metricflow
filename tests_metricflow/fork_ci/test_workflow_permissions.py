"""FORK: the fork's CI workflows give the `GITHUB_TOKEN` explicit, least-privilege permissions.

Each workflow sets a top-level `permissions: contents: read`, so no job depends on the repository's default token
permissions. The one job that pushes, `overwrite-snapshots` in `ci-metricflow-unit-tests.yaml`, keeps its own
`contents: write` block, which replaces the workflow-level one for that job.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pytest
import yaml

_WORKFLOWS_DIRECTORY = Path(__file__).resolve().parents[2] / ".github" / "workflows"
_WORKFLOW_FILE_NAMES = ["ci-cache-environments.yaml", "ci-linting.yaml", "ci-metricflow-unit-tests.yaml"]


def _load_workflow(file_name: str) -> Dict[str, object]:
    with open(_WORKFLOWS_DIRECTORY / file_name) as workflow_file:
        workflow = yaml.safe_load(workflow_file)
    assert isinstance(workflow, dict)
    return workflow


def test_every_workflow_is_checked() -> None:
    """A workflow added later is checked here too, or this test names it."""
    assert sorted(path.name for path in _WORKFLOWS_DIRECTORY.glob("*.y*ml")) == _WORKFLOW_FILE_NAMES


@pytest.mark.parametrize("file_name", _WORKFLOW_FILE_NAMES)
def test_workflow_token_is_read_only_by_default(file_name: str) -> None:
    """Every workflow sets a top-level `permissions: contents: read`."""
    assert _load_workflow(file_name).get("permissions") == {"contents": "read"}


def test_snapshot_job_can_push() -> None:
    """The snapshot job's own block keeps `contents: write`, which it needs to push the regenerated snapshots."""
    jobs = _load_workflow("ci-metricflow-unit-tests.yaml")["jobs"]
    assert isinstance(jobs, dict)
    assert jobs["overwrite-snapshots"]["permissions"] == {"contents": "write"}
