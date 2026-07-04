# SPDX-FileCopyrightText: © 2026 Tyler Nivin
# SPDX-License-Identifier: MIT

"""Kubernetes-level invariants for the generated Helm chart that `helm lint` doesn't check.

`helm lint` (run per-shape by tests/render-matrix.sh) validates chart structure and schema, but
not cross-field invariants like "a Deployment's selector must match its pod template's labels."
That invariant is exactly what chart.selectorLabels exists to protect (a hand-duplicated label
pair drifting apart would silently break rollouts — new pods are never adopted by the
Deployment — discovered only at apply time, not lint time).
"""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

import pytest
import yaml

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


@pytest.fixture(scope="module")
def helm_chart_dir(
    template_dir: Path,
    output_dir_module_scope: Path,
    render_template: Callable[..., Path],
) -> Path:
    """Render the full-modules shape (include_helm: true) and return the chart directory."""
    project_dir = render_template(
        template_dir,
        output_dir_module_scope,
        data={"project_name": "helm-chart-test", "include_helm": True},
        skip_tasks=True,
    )
    charts = [p for p in (project_dir / "helm").iterdir() if p.is_dir()]
    assert len(charts) == 1, f"expected exactly one chart under helm/, found {charts}"
    return charts[0]


@pytest.fixture(scope="module")
def helm_manifests(helm_chart_dir: Path) -> list[dict]:
    """Run `helm template` once and return the parsed manifests, shared by both tests below."""
    helm = shutil.which("helm")
    assert helm is not None, "helm not found on PATH"
    result = subprocess.run(  # noqa: S603
        [helm, "template", str(helm_chart_dir)],
        capture_output=True,
        text=True,
        check=True,
    )
    return [doc for doc in yaml.safe_load_all(result.stdout) if doc]


def test_deployment_selector_matches_template_labels(helm_manifests: list[dict]) -> None:
    """spec.selector.matchLabels must be a subset of spec.template.metadata.labels.

    Kubernetes rejects a Deployment update that changes an existing selector, and a selector
    that doesn't match its own pod template means the Deployment adopts no pods at all — both
    failure modes chart.selectorLabels exists to prevent by giving both sites one source of
    truth instead of two hand-duplicated label lists that could drift apart.
    """
    deployments = [doc for doc in helm_manifests if doc.get("kind") == "Deployment"]
    assert len(deployments) == 1, f"expected exactly one Deployment, found {len(deployments)}"

    selector_labels = deployments[0]["spec"]["selector"]["matchLabels"]
    template_labels = deployments[0]["spec"]["template"]["metadata"]["labels"]
    assert selector_labels.items() <= template_labels.items(), (
        f"selector {selector_labels} is not a subset of pod template labels {template_labels} "
        "— the Deployment would adopt no pods"
    )


def test_service_selector_matches_deployment_pods(helm_manifests: list[dict]) -> None:
    """The Service's selector must also route to the Deployment's pods.

    A Service and a Deployment are two independent template files that both hardcode (or, via
    chart.selectorLabels, both reference) the pod-identifying label pair — nothing but this
    test ties them together. A mismatch here means `kubectl get endpoints` shows zero
    addresses: the Service exists and looks healthy, but every request to it fails.
    """
    services = [doc for doc in helm_manifests if doc.get("kind") == "Service"]
    deployments = [doc for doc in helm_manifests if doc.get("kind") == "Deployment"]
    assert len(services) == 1, f"expected exactly one Service, found {len(services)}"
    assert len(deployments) == 1, f"expected exactly one Deployment, found {len(deployments)}"

    service_selector = services[0]["spec"]["selector"]
    pod_labels = deployments[0]["spec"]["template"]["metadata"]["labels"]
    assert service_selector.items() <= pod_labels.items(), (
        f"Service selector {service_selector} is not a subset of the Deployment's pod labels "
        f"{pod_labels} — the Service would route to nothing"
    )
