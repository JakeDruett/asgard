"""
Dockerfile Validator report builder.

Report building extracted from dockerfile_validator_helpers.py.
"""

import hashlib
import time
from typing import Dict, List

from Asgard.Volundr.Validation.models.validation_models import (
    FileValidationSummary,
    ValidationContext,
    ValidationReport,
    ValidationResult,
    ValidationSeverity,
)


def build_report(
    files: List[str],
    results: List[ValidationResult],
    start_time: float,
    context: ValidationContext,
) -> ValidationReport:
    """Build a ValidationReport from dockerfile validation results."""
    duration_ms = int((time.time() - start_time) * 1000)

    error_count = sum(1 for r in results if r.severity == ValidationSeverity.ERROR)
    warning_count = sum(1 for r in results if r.severity == ValidationSeverity.WARNING)
    info_count = sum(1 for r in results if r.severity in (ValidationSeverity.INFO, ValidationSeverity.HINT))

    score = 100.0
    score -= error_count * 10
    score -= warning_count * 3
    score -= info_count * 1
    score = max(0.0, score)

    file_summaries = []
    results_by_file: Dict[str, List[ValidationResult]] = {}
    for result in results:
        fp = result.file_path or "(no file)"
        if fp not in results_by_file:
            results_by_file[fp] = []
        results_by_file[fp].append(result)

    for fp in files:
        file_results = results_by_file.get(fp, [])
        file_errors = sum(1 for r in file_results if r.severity == ValidationSeverity.ERROR)
        file_warnings = sum(1 for r in file_results if r.severity == ValidationSeverity.WARNING)
        file_info = sum(1 for r in file_results if r.severity in (ValidationSeverity.INFO, ValidationSeverity.HINT))
        file_summaries.append(FileValidationSummary(
            file_path=fp,
            error_count=file_errors,
            warning_count=file_warnings,
            info_count=file_info,
            passed=file_errors == 0,
        ))

    report_id = hashlib.sha256(str(results).encode()).hexdigest()[:16]

    return ValidationReport(
        id=f"dockerfile-validation-{report_id}",
        title="Dockerfile Validation",
        validator="DockerfileValidator",
        results=results,
        file_summaries=file_summaries,
        total_files=len(files),
        total_errors=error_count,
        total_warnings=warning_count,
        total_info=info_count,
        passed=error_count == 0,
        score=score,
        duration_ms=duration_ms,
        context=context,
    )
