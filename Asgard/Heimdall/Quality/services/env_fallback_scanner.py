"""
Heimdall Environment Variable Fallback Scanner Service

Detects default/fallback values in environment variable and config/secret access
which violates the GAIA coding standard that prohibits setting fallback values
for environment variables and Vault secrets.

Detects:
- os.getenv("VAR", "default") - getenv with default parameter
- os.environ.get("VAR", "default") - environ.get with default parameter
- os.getenv("VAR") or "default" - getenv with 'or' fallback
- os.environ.get("VAR") or "default" - environ.get with 'or' fallback
- config.get("key", default) - config dict with default value
- shared.get("key", default) - shared dict with default value
- secrets.get("key", default) - secrets dict with default value
"""

import ast
import fnmatch
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from Asgard.Heimdall.Quality.models.env_fallback_models import (
    EnvFallbackConfig,
    EnvFallbackReport,
    EnvFallbackSeverity,
    EnvFallbackType,
    EnvFallbackViolation,
)


class EnvFallbackVisitor(ast.NodeVisitor):
    """
    AST visitor that detects environment variable fallback patterns.

    Walks the AST and identifies patterns where environment variables
    are accessed with default/fallback values.
    """

    def __init__(self, file_path: str, source_lines: List[str]):
        """
        Initialize the environment fallback visitor.

        Args:
            file_path: Path to the file being analyzed
            source_lines: Source code lines for extracting code text
        """
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: List[EnvFallbackViolation] = []
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None

    def _get_code_snippet(self, node: ast.AST) -> str:
        """Extract the code snippet from source."""
        if node.lineno <= len(self.source_lines):
            line = self.source_lines[node.lineno - 1].strip()
            return line
        return ""

    def _get_string_value(self, node: ast.AST) -> Optional[str]:
        """Extract string value from an AST node if it's a string literal."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.Str):  # Python 3.7 compatibility
            return node.s
        return None

    def _is_os_getenv(self, node: ast.Call) -> bool:
        """Check if call is os.getenv()."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "getenv":
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                    return True
        elif isinstance(node.func, ast.Name):
            # Direct getenv import: from os import getenv
            if node.func.id == "getenv":
                return True
        return False

    def _is_os_environ_get(self, node: ast.Call) -> bool:
        """Check if call is os.environ.get()."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "get":
                # Check for os.environ.get
                if isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == "environ":
                        if isinstance(node.func.value.value, ast.Name):
                            if node.func.value.value.id == "os":
                                return True
                # Check for environ.get (direct import)
                elif isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "environ":
                        return True
        return False

    def _get_env_var_name(self, call_node: ast.Call) -> Optional[str]:
        """Extract the environment variable name from a getenv/environ.get call."""
        if call_node.args:
            return self._get_string_value(call_node.args[0])
        return None

    def _get_default_value_repr(self, node: ast.AST) -> str:
        """Get a string representation of the default value."""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Str):
            return repr(node.s)
        elif isinstance(node, ast.Num):
            return repr(node.n)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.NameConstant):  # Python 3.7
            return repr(node.value)
        elif isinstance(node, ast.List):
            return "[...]"
        elif isinstance(node, ast.Dict):
            return "{...}"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return f"{node.func.id}(...)"
            elif isinstance(node.func, ast.Attribute):
                return f"...{node.func.attr}(...)"
        return "<expression>"

    def _record_violation(
        self,
        node: ast.AST,
        fallback_type: EnvFallbackType,
        variable_name: Optional[str],
        default_value: Optional[str],
    ) -> None:
        """Record an environment fallback violation."""
        severity = self._determine_severity(fallback_type)
        code_snippet = self._get_code_snippet(node)

        context_parts = []
        if self.current_class:
            context_parts.append(f"class {self.current_class}")
        if self.current_function:
            context_parts.append(f"function {self.current_function}")

        if context_parts:
            context = f"in {', '.join(context_parts)}"
        else:
            context = "at module level"

        # Determine context description based on fallback type
        config_types = {
            EnvFallbackType.CONFIG_GET_DEFAULT,
            EnvFallbackType.SECRETS_GET_DEFAULT,
            EnvFallbackType.VAULT_OR_FALLBACK,
        }
        if fallback_type in config_types:
            context_desc = f"Config/secrets fallback {context}"
        else:
            context_desc = f"Environment variable fallback {context}"

        self.violations.append(EnvFallbackViolation(
            file_path=self.file_path,
            line_number=node.lineno,
            column=getattr(node, 'col_offset', 0),
            code_snippet=code_snippet,
            variable_name=variable_name,
            default_value=default_value,
            fallback_type=fallback_type,
            severity=severity,
            containing_function=self.current_function,
            containing_class=self.current_class,
            context_description=context_desc,
        ))

    def _determine_severity(self, fallback_type: EnvFallbackType) -> EnvFallbackSeverity:
        """Determine severity based on fallback type."""
        high_severity = {
            EnvFallbackType.GETENV_DEFAULT,
            EnvFallbackType.ENVIRON_GET_DEFAULT,
            EnvFallbackType.CONFIG_GET_DEFAULT,
            EnvFallbackType.SECRETS_GET_DEFAULT,
        }
        medium_severity = {
            EnvFallbackType.GETENV_OR_FALLBACK,
            EnvFallbackType.ENVIRON_GET_OR_FALLBACK,
            EnvFallbackType.VAULT_OR_FALLBACK,
        }

        if fallback_type in high_severity:
            return EnvFallbackSeverity.HIGH
        elif fallback_type in medium_severity:
            return EnvFallbackSeverity.MEDIUM
        return EnvFallbackSeverity.LOW

    # Variable names that typically contain config/secrets from Vault
    CONFIG_VAR_NAMES = {
        "config", "cfg", "configuration", "conf",
        "shared", "service", "merged",
        "secrets", "secret", "credentials", "creds",
        "vault_data", "vault_secrets", "vault_config",
        "db_config", "database_config",
        "rabbitmq_config", "redis_config", "storage_config",
        "settings", "env_config",
    }

    def _is_config_dict_get(self, node: ast.Call) -> tuple[bool, Optional[str]]:
        """
        Check if call is a .get() on a config/secrets dictionary variable.

        Returns:
            Tuple of (is_config_get, variable_name)
        """
        if not isinstance(node.func, ast.Attribute):
            return False, None

        if node.func.attr != "get":
            return False, None

        # Check if it's a simple variable name
        if isinstance(node.func.value, ast.Name):
            var_name = node.func.value.id.lower()
            # Check if variable name suggests it's config/secrets
            for config_name in self.CONFIG_VAR_NAMES:
                if config_name in var_name:
                    return True, node.func.value.id
        return False, None

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls to detect getenv/environ.get with defaults."""
        # Check for os.getenv with default parameter
        if self._is_os_getenv(node):
            # Check for default argument (second positional or 'default' keyword)
            has_default = False
            default_value = None

            if len(node.args) >= 2:
                has_default = True
                default_value = self._get_default_value_repr(node.args[1])
            else:
                for kw in node.keywords:
                    if kw.arg == "default":
                        has_default = True
                        default_value = self._get_default_value_repr(kw.value)
                        break

            if has_default:
                var_name = self._get_env_var_name(node)
                self._record_violation(
                    node,
                    EnvFallbackType.GETENV_DEFAULT,
                    var_name,
                    default_value,
                )

        # Check for os.environ.get with default parameter
        elif self._is_os_environ_get(node):
            has_default = False
            default_value = None

            if len(node.args) >= 2:
                has_default = True
                default_value = self._get_default_value_repr(node.args[1])
            else:
                for kw in node.keywords:
                    if kw.arg == "default":
                        has_default = True
                        default_value = self._get_default_value_repr(kw.value)
                        break

            if has_default:
                var_name = self._get_env_var_name(node)
                self._record_violation(
                    node,
                    EnvFallbackType.ENVIRON_GET_DEFAULT,
                    var_name,
                    default_value,
                )

        # Check for config/secrets dict .get() with default
        else:
            is_config_get, config_var = self._is_config_dict_get(node)
            if is_config_get:
                has_default = False
                default_value = None
                key_name = None

                # Get the key being accessed
                if node.args:
                    key_name = self._get_string_value(node.args[0])

                # Check for default argument (second positional)
                if len(node.args) >= 2:
                    has_default = True
                    default_value = self._get_default_value_repr(node.args[1])
                else:
                    # Check for keyword argument
                    for kw in node.keywords:
                        if kw.arg == "default" or kw.arg is None:  # positional-only in some cases
                            has_default = True
                            default_value = self._get_default_value_repr(kw.value)
                            break

                if has_default:
                    # Determine if it's a secrets or config variable
                    var_lower = config_var.lower() if config_var else ""
                    if "secret" in var_lower or "cred" in var_lower:
                        fallback_type = EnvFallbackType.SECRETS_GET_DEFAULT
                    else:
                        fallback_type = EnvFallbackType.CONFIG_GET_DEFAULT

                    self._record_violation(
                        node,
                        fallback_type,
                        key_name,
                        default_value,
                    )

        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """Visit boolean operations to detect 'getenv(...) or default' patterns."""
        if isinstance(node.op, ast.Or) and len(node.values) >= 2:
            left = node.values[0]

            # Check if left side is a getenv/environ.get call
            if isinstance(left, ast.Call):
                if self._is_os_getenv(left):
                    # This is: os.getenv("VAR") or <fallback>
                    var_name = self._get_env_var_name(left)
                    default_value = self._get_default_value_repr(node.values[1])
                    self._record_violation(
                        node,
                        EnvFallbackType.GETENV_OR_FALLBACK,
                        var_name,
                        default_value,
                    )
                elif self._is_os_environ_get(left):
                    # This is: os.environ.get("VAR") or <fallback>
                    var_name = self._get_env_var_name(left)
                    default_value = self._get_default_value_repr(node.values[1])
                    self._record_violation(
                        node,
                        EnvFallbackType.ENVIRON_GET_OR_FALLBACK,
                        var_name,
                        default_value,
                    )

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition to track class context."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition to track function context."""
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition to track function context."""
        self._visit_function(node)

    def _visit_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
        """Common handler for function and async function definitions."""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function


class EnvFallbackScanner:
    """
    Scans Python files for environment variable fallback patterns.

    Detects patterns where environment variables are accessed with
    default/fallback values, which violates the GAIA coding standard.

    Usage:
        scanner = EnvFallbackScanner()
        report = scanner.analyze(Path("./src"))

        for violation in report.detected_violations:
            print(f"{violation.location}: {violation.code_snippet}")
    """

    def __init__(self, config: Optional[EnvFallbackConfig] = None):
        """
        Initialize environment fallback scanner.

        Args:
            config: Configuration for scanning. If None, uses defaults.
        """
        self.config = config or EnvFallbackConfig()

    def analyze(self, path: Path) -> EnvFallbackReport:
        """
        Analyze a file or directory for environment variable fallbacks.

        Args:
            path: Path to file or directory to analyze

        Returns:
            EnvFallbackReport with all detected violations

        Raises:
            FileNotFoundError: If path does not exist
        """
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        start_time = datetime.now()
        report = EnvFallbackReport(scan_path=str(path))

        if path.is_file():
            violations = self._analyze_file(path, path.parent)
            for violation in violations:
                report.add_violation(violation)
            report.files_scanned = 1
        else:
            self._analyze_directory(path, report)

        # Calculate scan duration
        report.scan_duration_seconds = (datetime.now() - start_time).total_seconds()

        # Calculate most problematic files
        file_violation_counts: Dict[str, int] = defaultdict(int)
        for violation in report.detected_violations:
            file_violation_counts[violation.file_path] += 1

        report.most_problematic_files = sorted(
            file_violation_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return report

    def analyze_single_file(self, file_path: Path) -> EnvFallbackReport:
        """
        Analyze a single file for environment variable fallbacks.

        Args:
            file_path: Path to Python file

        Returns:
            EnvFallbackReport with detected violations
        """
        return self.analyze(file_path)

    def _analyze_file(self, file_path: Path, root_path: Path) -> List[EnvFallbackViolation]:
        """
        Analyze a single file for environment variable fallbacks.

        Args:
            file_path: Path to Python file
            root_path: Root path for calculating relative paths

        Returns:
            List of detected violations
        """
        try:
            source = file_path.read_text(encoding="utf-8")
            source_lines = source.splitlines()
            tree = ast.parse(source)

            visitor = EnvFallbackVisitor(
                file_path=str(file_path.absolute()),
                source_lines=source_lines,
            )
            visitor.visit(tree)

            # Set relative paths
            for violation in visitor.violations:
                try:
                    violation.relative_path = str(file_path.relative_to(root_path))
                except ValueError:
                    violation.relative_path = file_path.name

            # Filter by severity
            filtered = [
                v for v in visitor.violations
                if self._severity_level(v.severity) >= self._severity_level(self.config.severity_filter)
            ]

            return filtered

        except SyntaxError:
            # Cannot parse file - skip it
            return []
        except Exception:
            # Other errors - skip file
            return []

    def _analyze_directory(self, directory: Path, report: EnvFallbackReport) -> None:
        """
        Analyze all Python files in a directory.

        Args:
            directory: Directory to analyze
            report: Report to add violations to
        """
        files_scanned = 0

        for root, dirs, files in os.walk(directory):
            root_path = Path(root)

            # Filter excluded directories
            dirs[:] = [
                d for d in dirs
                if not any(self._matches_pattern(d, pattern) for pattern in self.config.exclude_patterns)
            ]

            for file in files:
                # Check if file should be analyzed
                if not self._should_analyze_file(file):
                    continue

                # Check exclude patterns
                if any(self._matches_pattern(file, pattern) for pattern in self.config.exclude_patterns):
                    continue

                # Check test file inclusion
                if not self.config.include_tests:
                    if file.startswith("test_") or file.endswith("_test.py") or "tests" in str(root_path):
                        continue

                file_path = root_path / file
                violations = self._analyze_file(file_path, directory)
                files_scanned += 1

                for violation in violations:
                    report.add_violation(violation)

        report.files_scanned = files_scanned

    def _should_analyze_file(self, filename: str) -> bool:
        """Check if file should be analyzed based on extension."""
        if self.config.include_extensions:
            return any(filename.endswith(ext) for ext in self.config.include_extensions)
        return filename.endswith(".py")

    def _matches_pattern(self, name: str, pattern: str) -> bool:
        """Check if name matches exclude pattern."""
        return fnmatch.fnmatch(name, pattern)

    def _severity_level(self, severity: Union[str, EnvFallbackSeverity]) -> int:
        """Convert severity to numeric level for comparison."""
        if isinstance(severity, str):
            severity = EnvFallbackSeverity(severity)
        levels = {
            EnvFallbackSeverity.LOW: 1,
            EnvFallbackSeverity.MEDIUM: 2,
            EnvFallbackSeverity.HIGH: 3,
        }
        return levels.get(severity, 1)

    def generate_report(self, report: EnvFallbackReport, output_format: str = "text") -> str:
        """
        Generate formatted environment fallback report.

        Args:
            report: EnvFallbackReport to format
            output_format: Report format (text, json, markdown)

        Returns:
            Formatted report string

        Raises:
            ValueError: If output format is not supported
        """
        format_lower = output_format.lower()
        if format_lower == "json":
            return self._generate_json_report(report)
        elif format_lower == "markdown" or format_lower == "md":
            return self._generate_markdown_report(report)
        elif format_lower == "text":
            return self._generate_text_report(report)
        else:
            raise ValueError(f"Unsupported format: {output_format}. Use: text, json, markdown")

    def _generate_text_report(self, report: EnvFallbackReport) -> str:
        """Generate plain text report."""
        lines = [
            "=" * 70,
            "ENVIRONMENT VARIABLE FALLBACK VIOLATIONS REPORT",
            "=" * 70,
            "",
            f"Scan Path: {report.scan_path}",
            f"Scan Time: {report.scanned_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {report.scan_duration_seconds:.2f} seconds",
            f"Files Scanned: {report.files_scanned}",
            "",
            "SUMMARY",
            "-" * 40,
            f"Total Violations: {report.total_violations}",
            f"Compliant: {'Yes' if report.is_compliant else 'No'}",
            "",
        ]

        if report.has_violations:
            lines.extend(["By Severity:"])
            for severity in [EnvFallbackSeverity.HIGH, EnvFallbackSeverity.MEDIUM, EnvFallbackSeverity.LOW]:
                count = report.violations_by_severity.get(severity.value, 0)
                if count > 0:
                    lines.append(f"  {severity.value.upper()}: {count}")

            lines.extend(["", "By Type:"])
            for fallback_type in EnvFallbackType:
                count = report.violations_by_type.get(fallback_type.value, 0)
                if count > 0:
                    type_display = fallback_type.value.replace('_', ' ').title()
                    lines.append(f"  {type_display}: {count}")

            if report.most_problematic_files:
                lines.extend(["", "Most Problematic Files:", "-" * 40])
                for file_path, count in report.most_problematic_files[:5]:
                    filename = os.path.basename(file_path)
                    lines.append(f"  {filename}: {count} violations")

            lines.extend(["", "VIOLATIONS", "-" * 40])

            # Group by severity
            for severity in [EnvFallbackSeverity.HIGH, EnvFallbackSeverity.MEDIUM, EnvFallbackSeverity.LOW]:
                severity_violations = report.get_violations_by_severity(severity)
                if severity_violations:
                    lines.extend(["", f"[{severity.value.upper()}]"])
                    for violation in severity_violations:
                        lines.append(f"  {violation.location}")
                        lines.append(f"    Code: {violation.code_snippet}")
                        if violation.variable_name:
                            lines.append(f"    Variable: {violation.variable_name}")
                        if violation.default_value:
                            lines.append(f"    Default: {violation.default_value}")
                        lines.append(f"    Context: {violation.context_description}")
                        lines.append(f"    Fix: {violation.remediation}")
                        lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    def _generate_json_report(self, report: EnvFallbackReport) -> str:
        """Generate JSON report."""
        violations_data = []
        for v in report.detected_violations:
            violations_data.append({
                "file_path": v.file_path,
                "relative_path": v.relative_path,
                "line_number": v.line_number,
                "column": v.column,
                "code_snippet": v.code_snippet,
                "variable_name": v.variable_name,
                "default_value": v.default_value,
                "fallback_type": v.fallback_type if isinstance(v.fallback_type, str) else v.fallback_type.value,
                "severity": v.severity if isinstance(v.severity, str) else v.severity.value,
                "containing_function": v.containing_function,
                "containing_class": v.containing_class,
                "context_description": v.context_description,
                "remediation": v.remediation,
            })

        report_data = {
            "scan_info": {
                "scan_path": report.scan_path,
                "scanned_at": report.scanned_at.isoformat(),
                "duration_seconds": report.scan_duration_seconds,
                "files_scanned": report.files_scanned,
            },
            "summary": {
                "total_violations": report.total_violations,
                "is_compliant": report.is_compliant,
                "violations_by_severity": report.violations_by_severity,
                "violations_by_type": report.violations_by_type,
            },
            "violations": violations_data,
            "most_problematic_files": [
                {"file": file_path, "violation_count": count}
                for file_path, count in report.most_problematic_files
            ],
        }

        return json.dumps(report_data, indent=2)

    def _generate_markdown_report(self, report: EnvFallbackReport) -> str:
        """Generate Markdown report."""
        lines = [
            "# Environment Variable Fallback Violations Report",
            "",
            f"**Scan Path:** `{report.scan_path}`",
            f"**Generated:** {report.scanned_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Duration:** {report.scan_duration_seconds:.2f} seconds",
            f"**Files Scanned:** {report.files_scanned}",
            "",
            "## Summary",
            "",
            f"**Total Violations:** {report.total_violations}",
            f"**Compliant:** {'Yes' if report.is_compliant else 'No'}",
            "",
        ]

        if report.has_violations:
            lines.extend([
                "### By Severity",
                "",
                "| Severity | Count |",
                "|----------|-------|",
            ])
            for severity in [EnvFallbackSeverity.HIGH, EnvFallbackSeverity.MEDIUM, EnvFallbackSeverity.LOW]:
                count = report.violations_by_severity.get(severity.value, 0)
                lines.append(f"| {severity.value.title()} | {count} |")

            lines.extend([
                "",
                "### By Type",
                "",
                "| Type | Count |",
                "|------|-------|",
            ])
            for fallback_type in EnvFallbackType:
                count = report.violations_by_type.get(fallback_type.value, 0)
                if count > 0:
                    type_display = fallback_type.value.replace('_', ' ').title()
                    lines.append(f"| {type_display} | {count} |")

            if report.most_problematic_files:
                lines.extend(["", "## Most Problematic Files", ""])
                for file_path, count in report.most_problematic_files[:10]:
                    filename = os.path.basename(file_path)
                    lines.append(f"- `{filename}`: {count} violations")

            lines.extend(["", "## Violations", ""])

            for severity in [EnvFallbackSeverity.HIGH, EnvFallbackSeverity.MEDIUM, EnvFallbackSeverity.LOW]:
                severity_violations = report.get_violations_by_severity(severity)
                if severity_violations:
                    lines.extend([f"### {severity.value.title()} Severity", ""])

                    for v in severity_violations[:50]:
                        filename = os.path.basename(v.file_path)
                        lines.extend([
                            f"#### `{filename}:{v.line_number}`",
                            "",
                            f"**Code:** `{v.code_snippet}`",
                            "",
                        ])
                        if v.variable_name:
                            lines.append(f"**Variable:** `{v.variable_name}`")
                        if v.default_value:
                            lines.append(f"**Default Value:** `{v.default_value}`")
                        lines.extend([
                            "",
                            f"**Context:** {v.context_description}",
                            "",
                            f"**Remediation:** {v.remediation}",
                            "",
                        ])

        return "\n".join(lines)
