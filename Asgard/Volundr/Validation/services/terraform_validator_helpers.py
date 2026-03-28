import os
import re
from typing import List

from Asgard.Volundr.Validation.models.validation_models import (
    ValidationCategory,
    ValidationResult,
    ValidationSeverity,
)

SENSITIVE_PATTERNS = [
    "password", "secret", "key", "token", "api_key", "apikey",
    "auth", "credential", "private", "cert", "ssh",
]


def validate_variable(
    content: str, var_name: str, file_path: str, line_num: int, start_pos: int
) -> List[ValidationResult]:
    results: List[ValidationResult] = []

    block_content = extract_block(content, start_pos)

    if 'description' not in block_content:
        results.append(ValidationResult(
            rule_id="variable-no-description",
            message=f"Variable '{var_name}' missing description",
            severity=ValidationSeverity.WARNING,
            category=ValidationCategory.MAINTAINABILITY,
            file_path=file_path,
            line_number=line_num,
            suggestion="Add a description for documentation",
        ))

    if 'type' not in block_content:
        results.append(ValidationResult(
            rule_id="variable-no-type",
            message=f"Variable '{var_name}' missing type constraint",
            severity=ValidationSeverity.WARNING,
            category=ValidationCategory.BEST_PRACTICE,
            file_path=file_path,
            line_number=line_num,
            suggestion="Add a type constraint for better validation",
        ))

    if any(p in var_name.lower() for p in SENSITIVE_PATTERNS):
        if 'sensitive' not in block_content or 'sensitive = true' not in block_content:
            results.append(ValidationResult(
                rule_id="variable-not-sensitive",
                message=f"Variable '{var_name}' appears to be sensitive but not marked as such",
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.SECURITY,
                file_path=file_path,
                line_number=line_num,
                suggestion="Add 'sensitive = true' to the variable",
            ))

    return results


def validate_output(
    content: str, output_name: str, file_path: str, line_num: int, start_pos: int
) -> List[ValidationResult]:
    results: List[ValidationResult] = []

    block_content = extract_block(content, start_pos)

    if 'description' not in block_content:
        results.append(ValidationResult(
            rule_id="output-no-description",
            message=f"Output '{output_name}' missing description",
            severity=ValidationSeverity.INFO,
            category=ValidationCategory.MAINTAINABILITY,
            file_path=file_path,
            line_number=line_num,
        ))

    if any(p in output_name.lower() for p in SENSITIVE_PATTERNS):
        if 'sensitive' not in block_content or 'sensitive = true' not in block_content:
            results.append(ValidationResult(
                rule_id="output-not-sensitive",
                message=f"Output '{output_name}' appears to be sensitive but not marked as such",
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.SECURITY,
                file_path=file_path,
                line_number=line_num,
                suggestion="Add 'sensitive = true' to the output",
            ))

    return results


def validate_module_call(
    content: str, module_name: str, file_path: str, line_num: int, start_pos: int
) -> List[ValidationResult]:
    results: List[ValidationResult] = []

    block_content = extract_block(content, start_pos)

    if 'source' not in block_content:
        results.append(ValidationResult(
            rule_id="module-no-source",
            message=f"Module '{module_name}' missing source",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.SCHEMA,
            file_path=file_path,
            line_number=line_num,
        ))

    if 'registry.terraform.io' in block_content or ('source' in block_content and 'version' not in block_content):
        source_match = re.search(r'source\s*=\s*"([^"]+)"', block_content)
        if source_match:
            source = source_match.group(1)
            if not source.startswith('./') and not source.startswith('../') and '://' not in source:
                if 'version' not in block_content:
                    results.append(ValidationResult(
                        rule_id="module-no-version",
                        message=f"Module '{module_name}' should pin version for registry module",
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.BEST_PRACTICE,
                        file_path=file_path,
                        line_number=line_num,
                        suggestion="Add version constraint for reproducible builds",
                    ))

    return results


def validate_module_structure(
    directory: str, files: List[str]
) -> List[ValidationResult]:
    results: List[ValidationResult] = []
    file_names = [os.path.basename(f) for f in files]

    if "main.tf" not in file_names:
        results.append(ValidationResult(
            rule_id="missing-main-tf",
            message="Module missing main.tf file",
            severity=ValidationSeverity.INFO,
            category=ValidationCategory.BEST_PRACTICE,
            file_path=directory,
        ))

    if "variables.tf" not in file_names:
        results.append(ValidationResult(
            rule_id="missing-variables-tf",
            message="Module missing variables.tf file",
            severity=ValidationSeverity.INFO,
            category=ValidationCategory.BEST_PRACTICE,
            file_path=directory,
        ))

    if "outputs.tf" not in file_names:
        results.append(ValidationResult(
            rule_id="missing-outputs-tf",
            message="Module missing outputs.tf file",
            severity=ValidationSeverity.INFO,
            category=ValidationCategory.BEST_PRACTICE,
            file_path=directory,
        ))

    return results


def check_hardcoded_credentials(
    content: str, file_path: str, lines: List[str]
) -> List[ValidationResult]:
    results: List[ValidationResult] = []

    patterns = [
        (r'access_key\s*=\s*"[A-Z0-9]{20}"', "AWS access key"),
        (r'secret_key\s*=\s*"[A-Za-z0-9/+=]{40}"', "AWS secret key"),
        (r'password\s*=\s*"[^"]+"', "hardcoded password"),
        (r'api_key\s*=\s*"[^"]+"', "hardcoded API key"),
    ]

    for i, line in enumerate(lines):
        for pattern, description in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                results.append(ValidationResult(
                    rule_id="hardcoded-credential",
                    message=f"Possible {description} found",
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SECURITY,
                    file_path=file_path,
                    line_number=i + 1,
                    suggestion="Use variables or environment variables for sensitive values",
                ))

    return results


def check_deprecated_syntax(
    content: str, file_path: str, lines: List[str]
) -> List[ValidationResult]:
    results: List[ValidationResult] = []

    for i, line in enumerate(lines):
        if re.search(r'=\s*"\$\{[^}]+\}"$', line.strip()):
            results.append(ValidationResult(
                rule_id="deprecated-interpolation",
                message="Unnecessary interpolation syntax (deprecated in Terraform 0.12+)",
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.BEST_PRACTICE,
                file_path=file_path,
                line_number=i + 1,
                suggestion="Use direct reference instead of interpolation",
            ))

    return results


def extract_block(content: str, start_pos: int) -> str:
    brace_count = 0
    started = False
    end_pos = start_pos

    for i in range(start_pos, len(content)):
        char = content[i]
        if char == '{':
            brace_count += 1
            started = True
        elif char == '}':
            brace_count -= 1
            if started and brace_count == 0:
                end_pos = i + 1
                break

    return content[start_pos:end_pos]


