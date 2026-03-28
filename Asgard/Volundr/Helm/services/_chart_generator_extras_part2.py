"""Helm chart validation and scoring functions."""

from typing import Dict, List

from Asgard.Volundr.Helm.models.helm_models import HelmConfig


def validate_chart(chart_files: Dict[str, str], config: HelmConfig) -> List[str]:
    issues: List[str] = []
    if "Chart.yaml" not in chart_files:
        issues.append("Missing Chart.yaml")
    if "values.yaml" not in chart_files:
        issues.append("Missing values.yaml")
    if "templates/deployment.yaml" not in chart_files:
        issues.append("Missing deployment template")
    if "templates/_helpers.tpl" not in chart_files:
        issues.append("Missing _helpers.tpl - chart naming may be inconsistent")
    chart_yaml = chart_files.get("Chart.yaml", "")
    if "version:" not in chart_yaml:
        issues.append("Chart.yaml missing version")
    if "appVersion:" not in chart_yaml:
        issues.append("Chart.yaml missing appVersion")
    values_yaml = chart_files.get("values.yaml", "")
    if "resources:" not in values_yaml:
        issues.append("values.yaml missing resource definitions")
    return issues


def calculate_best_practice_score(chart_files: Dict[str, str], config: HelmConfig) -> float:
    score = 0.0
    max_score = 0.0
    max_score += 20
    essential_files = ["Chart.yaml", "values.yaml", "templates/deployment.yaml", "templates/service.yaml"]
    for f in essential_files:
        if f in chart_files:
            score += 5
    max_score += 10
    if "templates/_helpers.tpl" in chart_files:
        score += 10
    max_score += 15
    values_yaml = chart_files.get("values.yaml", "")
    if "securityContext:" in values_yaml:
        score += 15
    max_score += 15
    if "resources:" in values_yaml and "limits:" in values_yaml:
        score += 15
    max_score += 15
    if "livenessProbe:" in values_yaml and "readinessProbe:" in values_yaml:
        score += 15
    max_score += 10
    if "templates/serviceaccount.yaml" in chart_files:
        score += 10
    max_score += 10
    if "templates/tests/test-connection.yaml" in chart_files:
        score += 10
    max_score += 5
    if "templates/NOTES.txt" in chart_files:
        score += 5
    return (score / max_score) * 100 if max_score > 0 else 0.0
