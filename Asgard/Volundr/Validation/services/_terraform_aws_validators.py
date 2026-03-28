"""
Terraform AWS resource validators.

AWS-specific validation functions extracted from terraform_validator_helpers.py.
"""

import re
from typing import List

from Asgard.Volundr.Validation.models.validation_models import (
    ValidationCategory,
    ValidationResult,
    ValidationSeverity,
)


def validate_aws_security_group(
    content: str, name: str, file_path: str, line_num: int
) -> List[ValidationResult]:
    results: List[ValidationResult] = []

    if '0.0.0.0/0' in content and ('ingress' in content.lower()):
        results.append(ValidationResult(
            rule_id="sg-open-ingress",
            message=f"Security group '{name}' allows ingress from 0.0.0.0/0",
            severity=ValidationSeverity.WARNING,
            category=ValidationCategory.SECURITY,
            file_path=file_path,
            line_number=line_num,
            resource_name=name,
            suggestion="Restrict ingress to specific CIDR blocks",
        ))

    if 'from_port = 0' in content and 'to_port = 65535' in content:
        results.append(ValidationResult(
            rule_id="sg-all-ports",
            message=f"Security group '{name}' opens all ports",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.SECURITY,
            file_path=file_path,
            line_number=line_num,
            resource_name=name,
        ))

    return results


def validate_aws_s3_bucket(
    content: str, name: str, file_path: str, line_num: int
) -> List[ValidationResult]:
    results: List[ValidationResult] = []

    if 'versioning' not in content.lower():
        results.append(ValidationResult(
            rule_id="s3-no-versioning",
            message=f"S3 bucket '{name}' may not have versioning enabled",
            severity=ValidationSeverity.INFO,
            category=ValidationCategory.BEST_PRACTICE,
            file_path=file_path,
            line_number=line_num,
            resource_name=name,
            suggestion="Consider enabling versioning for data protection",
        ))

    if 'server_side_encryption' not in content.lower() and 'aws_s3_bucket_server_side_encryption_configuration' not in content:
        results.append(ValidationResult(
            rule_id="s3-no-encryption",
            message=f"S3 bucket '{name}' may not have encryption configured",
            severity=ValidationSeverity.WARNING,
            category=ValidationCategory.SECURITY,
            file_path=file_path,
            line_number=line_num,
            resource_name=name,
            suggestion="Enable server-side encryption",
        ))

    return results


def validate_aws_iam_policy(
    content: str, name: str, file_path: str, line_num: int
) -> List[ValidationResult]:
    results: List[ValidationResult] = []

    if '"Action": "*"' in content or "'Action': '*'" in content or 'Action = "*"' in content:
        results.append(ValidationResult(
            rule_id="iam-wildcard-action",
            message=f"IAM policy '{name}' uses wildcard (*) action",
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.SECURITY,
            file_path=file_path,
            line_number=line_num,
            resource_name=name,
            suggestion="Use specific actions instead of wildcard",
        ))

    if '"Resource": "*"' in content or "'Resource': '*'" in content or 'Resource = "*"' in content:
        results.append(ValidationResult(
            rule_id="iam-wildcard-resource",
            message=f"IAM policy '{name}' uses wildcard (*) resource",
            severity=ValidationSeverity.WARNING,
            category=ValidationCategory.SECURITY,
            file_path=file_path,
            line_number=line_num,
            resource_name=name,
            suggestion="Scope resources to specific ARNs",
        ))

    return results
