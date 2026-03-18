"""
Heimdall Type Checker Service

Static type checking analysis using Pyright (Pylance engine).
Provides full Pylance-equivalent type checking across the entire codebase,
not just open files.

Features (Pylance/Pyright parity):
- Type inference and validation
- Type compatibility/assignability checking
- Missing/undefined attribute detection
- Incorrect argument types/counts
- Return type mismatches
- Union type narrowing
- Generic type validation
- Protocol conformance
- TypedDict validation
- Overload resolution
- Import resolution errors
- Unreachable code detection (type-based)
- Optional/None safety checks
- Deprecated API usage detection
"""

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from Asgard.Heimdall.Quality.models.type_check_models import (
    RULE_CATEGORY_MAP,
    FileTypeCheckStats,
    TypeCheckCategory,
    TypeCheckConfig,
    TypeCheckDiagnostic,
    TypeCheckReport,
    TypeCheckSeverity,
)


class TypeChecker:
    """
    Static type checker wrapping Pyright for Pylance-equivalent analysis.

    Runs Pyright over the entire codebase (not just open files like Pylance)
    and produces structured reports compatible with Heimdall's reporting framework.

    Usage:
        checker = TypeChecker()
        report = checker.analyze(Path("./src"))

        print(f"Errors: {report.total_errors}")
        print(f"Warnings: {report.total_warnings}")
        for diag in report.all_diagnostics:
            print(f"  {diag.qualified_location}: {diag.message}")
    """

    def __init__(self, config: Optional[TypeCheckConfig] = None):
        """
        Initialize type checker.

        Args:
            config: Configuration for type checking. If None, uses defaults.
        """
        self.config = config or TypeCheckConfig()

    def analyze(self, path: Path) -> TypeCheckReport:
        """
        Run Pyright type checking on a file or directory.

        Args:
            path: Path to file or directory to analyze

        Returns:
            TypeCheckReport with all diagnostics

        Raises:
            FileNotFoundError: If path does not exist
            RuntimeError: If pyright is not available
        """
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        self._verify_pyright_available()

        start_time = datetime.now()
        report = TypeCheckReport(
            scan_path=str(path),
            type_checking_mode=self.config.type_checking_mode,
        )

        # Run pyright and parse output
        pyright_output = self._run_pyright(path)
        self._parse_pyright_output(pyright_output, path, report)

        report.scan_duration_seconds = (datetime.now() - start_time).total_seconds()

        return report

    def _verify_pyright_available(self) -> None:
        """Verify that pyright is available via npx."""
        try:
            result = subprocess.run(
                [self.config.npx_path, "pyright", "--version"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                # Extract version number
                if "pyright" in version.lower():
                    self._pyright_version = version.split()[-1] if version.split() else version
                else:
                    self._pyright_version = version
            else:
                raise RuntimeError(
                    "Pyright is not available. Install with: npm install -g pyright"
                )
        except FileNotFoundError:
            raise RuntimeError(
                f"npx not found at '{self.config.npx_path}'. "
                "Install Node.js or set npx_path in config."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Pyright version check timed out.")

    def _build_pyright_config(self, path: Path) -> Optional[str]:
        """
        Build a temporary pyrightconfig.json for the analysis.

        Returns path to temp config file, or None to use defaults.
        """
        config_data = {
            "typeCheckingMode": self.config.type_checking_mode,
        }

        if self.config.python_version:
            config_data["pythonVersion"] = self.config.python_version

        if self.config.python_platform:
            config_data["pythonPlatform"] = self.config.python_platform

        if self.config.venv_path:
            config_data["venvPath"] = str(Path(self.config.venv_path).parent)
            config_data["venv"] = Path(self.config.venv_path).name

        # Build exclude list
        excludes = list(self.config.exclude_patterns)
        if not self.config.include_tests:
            excludes.extend(["**/test_*.py", "**/*_test.py", "**/tests/", "**/Hercules/"])

        if excludes:
            config_data["exclude"] = excludes

        return config_data

    def _run_pyright(self, path: Path) -> dict:
        """
        Run pyright on the given path and return parsed JSON output.

        Args:
            path: Path to analyze

        Returns:
            Parsed JSON output from pyright
        """
        # Build command
        cmd = [self.config.npx_path, "pyright", "--outputjson"]

        # Create temp config if needed
        config_data = self._build_pyright_config(path)
        temp_config_path = None

        try:
            if config_data:
                # Write temp config to the target directory
                if path.is_dir():
                    config_dir = path
                else:
                    config_dir = path.parent

                temp_config_path = config_dir / ".pyrightconfig.heimdall.json"
                existing_config = config_dir / "pyrightconfig.json"
                has_existing = existing_config.exists()

                if not has_existing:
                    # No existing config - write ours as pyrightconfig.json
                    temp_config_path = existing_config
                    with open(temp_config_path, "w") as f:
                        json.dump(config_data, f, indent=2)
                else:
                    # Existing config present - use --project flag with temp file
                    with open(temp_config_path, "w") as f:
                        json.dump(config_data, f, indent=2)
                    cmd.extend(["--project", str(temp_config_path)])

            # Add path to analyze
            cmd.append(str(path))

            # Run pyright
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout for large codebases
                cwd=str(path) if path.is_dir() else str(path.parent),
            )

            # Parse JSON output
            if result.stdout:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Try to find JSON in output (pyright sometimes has preamble)
                    for line in result.stdout.split("\n"):
                        line = line.strip()
                        if line.startswith("{"):
                            try:
                                return json.loads(line)
                            except json.JSONDecodeError:
                                continue

            # If we can't parse output, return empty result
            return {
                "version": getattr(self, "_pyright_version", "unknown"),
                "generalDiagnostics": [],
                "summary": {
                    "filesAnalyzed": 0,
                    "errorCount": 0,
                    "warningCount": 0,
                    "informationCount": 0,
                    "timeInSec": 0,
                },
            }

        finally:
            # Clean up temp config
            if temp_config_path and temp_config_path.exists():
                if temp_config_path.name in (".pyrightconfig.heimdall.json", "pyrightconfig.json"):
                    try:
                        temp_config_path.unlink()
                    except OSError:
                        pass

    def _parse_pyright_output(self, output: dict, scan_path: Path, report: TypeCheckReport) -> None:
        """
        Parse pyright JSON output into the report.

        Args:
            output: Parsed JSON from pyright
            scan_path: Root scan path for relative paths
            report: Report to populate
        """
        # Extract version
        report.pyright_version = output.get("version", getattr(self, "_pyright_version", "unknown"))

        # Extract summary
        summary = output.get("summary", {})
        report.files_scanned = summary.get("filesAnalyzed", 0)
        report.exit_code = output.get("exitCode", 0) if "exitCode" in output else (1 if summary.get("errorCount", 0) > 0 else 0)

        # Parse diagnostics
        diagnostics = output.get("generalDiagnostics", [])
        file_diagnostics: Dict[str, List[TypeCheckDiagnostic]] = {}

        for diag in diagnostics:
            severity_str = diag.get("severity", "error").lower()

            # Apply severity filter
            if self.config.severity_filter:
                if severity_str != self.config.severity_filter:
                    continue

            # Skip info-level if not including warnings
            if not self.config.include_warnings and severity_str != "error":
                continue

            # Map severity
            severity = TypeCheckSeverity.ERROR
            if severity_str == "warning":
                severity = TypeCheckSeverity.WARNING
            elif severity_str == "information":
                severity = TypeCheckSeverity.INFORMATION

            # Extract location
            file_path = diag.get("file", "")
            range_data = diag.get("range", {})
            start = range_data.get("start", {})
            end = range_data.get("end", {})

            # Calculate relative path
            try:
                relative_path = str(Path(file_path).relative_to(scan_path))
            except (ValueError, TypeError):
                relative_path = os.path.basename(file_path) if file_path else ""

            # Determine rule and category
            rule = diag.get("rule", "")
            category = RULE_CATEGORY_MAP.get(rule, TypeCheckCategory.GENERAL)

            # Apply category filter
            if self.config.category_filter:
                if category.value != self.config.category_filter and category != self.config.category_filter:
                    continue

            diagnostic = TypeCheckDiagnostic(
                file_path=file_path,
                relative_path=relative_path,
                line=start.get("line", 0) + 1,  # pyright uses 0-based lines
                column=start.get("character", 0),
                end_line=end.get("line", 0) + 1,
                end_column=end.get("character", 0),
                severity=severity,
                message=diag.get("message", ""),
                rule=rule,
                category=category,
            )

            report.add_diagnostic(diagnostic)

            # Group by file
            if file_path not in file_diagnostics:
                file_diagnostics[file_path] = []
            file_diagnostics[file_path].append(diagnostic)

        # Build file stats
        for file_path, diags in file_diagnostics.items():
            try:
                relative_path = str(Path(file_path).relative_to(scan_path))
            except (ValueError, TypeError):
                relative_path = os.path.basename(file_path) if file_path else ""

            file_stats = FileTypeCheckStats(
                file_path=file_path,
                relative_path=relative_path,
                error_count=sum(1 for d in diags if d.severity == TypeCheckSeverity.ERROR.value),
                warning_count=sum(1 for d in diags if d.severity == TypeCheckSeverity.WARNING.value),
                info_count=sum(1 for d in diags if d.severity == TypeCheckSeverity.INFORMATION.value),
                diagnostics=diags,
            )
            report.add_file_stats(file_stats)

    def generate_report(self, report: TypeCheckReport, output_format: str = "text") -> str:
        """
        Generate formatted type checking report.

        Args:
            report: TypeCheckReport to format
            output_format: Report format (text, json, markdown)

        Returns:
            Formatted report string
        """
        format_lower = output_format.lower()
        if format_lower == "json":
            return self._generate_json_report(report)
        elif format_lower in ("markdown", "md"):
            return self._generate_markdown_report(report)
        elif format_lower == "text":
            return self._generate_text_report(report)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _generate_text_report(self, report: TypeCheckReport) -> str:
        """Generate plain text report."""
        lines = [
            "=" * 70,
            "STATIC TYPE CHECKING REPORT (Pyright/Pylance Engine)",
            "=" * 70,
            "",
            f"Scan Path: {report.scan_path}",
            f"Scan Time: {report.scanned_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {report.scan_duration_seconds:.2f} seconds",
            f"Pyright Version: {report.pyright_version}",
            f"Type Checking Mode: {report.type_checking_mode}",
            f"Files Analyzed: {report.files_scanned}",
            "",
            "SUMMARY",
            "-" * 50,
            f"Total Errors: {report.total_errors}",
            f"Total Warnings: {report.total_warnings}",
            f"Total Info: {report.total_info}",
            f"Files With Errors: {report.files_with_errors}",
            f"Status: {'PASSING' if report.is_compliant else 'FAILING'}",
            "",
        ]

        # Category breakdown
        if report.errors_by_category:
            lines.extend(["ERRORS BY CATEGORY", "-" * 50])
            for cat, count in sorted(report.errors_by_category.items(), key=lambda x: x[1], reverse=True):
                cat_label = cat.replace("_", " ").title()
                lines.append(f"  {cat_label:<30} {count:>5}")
            lines.append("")

        # Rule breakdown (top 20)
        if report.errors_by_rule:
            lines.extend(["TOP RULES", "-" * 50])
            sorted_rules = sorted(report.errors_by_rule.items(), key=lambda x: x[1], reverse=True)[:20]
            for rule, count in sorted_rules:
                lines.append(f"  {rule:<45} {count:>5}")
            lines.append("")

        # Most problematic files
        problem_files = report.get_most_problematic_files(20)
        if problem_files:
            lines.extend(["MOST PROBLEMATIC FILES", "-" * 50])
            for f in problem_files:
                lines.append(
                    f"  {f.relative_path:<55} E:{f.error_count:>3} W:{f.warning_count:>3}"
                )
            lines.append("")

        # Detailed diagnostics (grouped by file)
        if report.all_diagnostics:
            lines.extend(["DIAGNOSTICS", "-" * 50])

            # Group by file
            by_file: Dict[str, List[TypeCheckDiagnostic]] = {}
            for diag in report.all_diagnostics:
                key = diag.relative_path or diag.file_path
                if key not in by_file:
                    by_file[key] = []
                by_file[key].append(diag)

            for file_path in sorted(by_file.keys()):
                diags = by_file[file_path]
                lines.append(f"\n  {file_path}")
                for diag in sorted(diags, key=lambda d: d.line):
                    sev_marker = {
                        "error": "[ERROR]",
                        "warning": "[WARN] ",
                        "information": "[INFO] ",
                    }.get(diag.severity, "[????] ")
                    rule_suffix = f" ({diag.rule})" if diag.rule else ""
                    lines.append(
                        f"    L{diag.line}:{diag.column} {sev_marker} {diag.message}{rule_suffix}"
                    )

        lines.extend(["", "=" * 70])
        return "\n".join(lines)

    def _generate_json_report(self, report: TypeCheckReport) -> str:
        """Generate JSON report."""
        report_data = {
            "scan_info": {
                "scan_path": report.scan_path,
                "scanned_at": report.scanned_at.isoformat(),
                "duration_seconds": report.scan_duration_seconds,
                "pyright_version": report.pyright_version,
                "type_checking_mode": report.type_checking_mode,
                "files_analyzed": report.files_scanned,
            },
            "summary": {
                "total_errors": report.total_errors,
                "total_warnings": report.total_warnings,
                "total_info": report.total_info,
                "files_with_errors": report.files_with_errors,
                "is_passing": report.is_compliant,
                "errors_by_category": report.errors_by_category,
                "errors_by_rule": report.errors_by_rule,
            },
            "files": [
                {
                    "file_path": f.file_path,
                    "relative_path": f.relative_path,
                    "error_count": f.error_count,
                    "warning_count": f.warning_count,
                    "info_count": f.info_count,
                }
                for f in report.files_analyzed
            ],
            "diagnostics": [
                {
                    "file_path": d.file_path,
                    "relative_path": d.relative_path,
                    "line": d.line,
                    "column": d.column,
                    "end_line": d.end_line,
                    "end_column": d.end_column,
                    "severity": d.severity,
                    "message": d.message,
                    "rule": d.rule,
                    "category": d.category,
                }
                for d in report.all_diagnostics
            ],
        }
        return json.dumps(report_data, indent=2)

    def _generate_markdown_report(self, report: TypeCheckReport) -> str:
        """Generate Markdown report."""
        status = "PASS" if report.is_compliant else "FAIL"

        lines = [
            "# Static Type Checking Report",
            "",
            f"**Engine:** Pyright {report.pyright_version} (Pylance equivalent)",
            f"**Mode:** `{report.type_checking_mode}`",
            f"**Scan Path:** `{report.scan_path}`",
            f"**Generated:** {report.scanned_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Files Analyzed:** {report.files_scanned}",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Errors | {report.total_errors} |",
            f"| Total Warnings | {report.total_warnings} |",
            f"| Total Info | {report.total_info} |",
            f"| Files With Errors | {report.files_with_errors} |",
            f"| **Status** | **{status}** |",
            "",
        ]

        # Category breakdown
        if report.errors_by_category:
            lines.extend([
                "## Issues by Category",
                "",
                "| Category | Count |",
                "|----------|-------|",
            ])
            for cat, count in sorted(report.errors_by_category.items(), key=lambda x: x[1], reverse=True):
                cat_label = cat.replace("_", " ").title()
                lines.append(f"| {cat_label} | {count} |")
            lines.append("")

        # Top rules
        if report.errors_by_rule:
            lines.extend([
                "## Top Pyright Rules Triggered",
                "",
                "| Rule | Count |",
                "|------|-------|",
            ])
            for rule, count in sorted(report.errors_by_rule.items(), key=lambda x: x[1], reverse=True)[:20]:
                lines.append(f"| `{rule}` | {count} |")
            lines.append("")

        # Most problematic files
        problem_files = report.get_most_problematic_files(20)
        if problem_files:
            lines.extend([
                "## Most Problematic Files",
                "",
                "| File | Errors | Warnings |",
                "|------|--------|----------|",
            ])
            for f in problem_files:
                lines.append(f"| `{f.relative_path}` | {f.error_count} | {f.warning_count} |")
            lines.append("")

        # Detailed diagnostics (first 100)
        if report.all_diagnostics:
            lines.extend([
                "## Diagnostics",
                "",
            ])
            for diag in report.all_diagnostics[:100]:
                sev = diag.severity.upper() if isinstance(diag.severity, str) else diag.severity
                rule_note = f" (`{diag.rule}`)" if diag.rule else ""
                lines.extend([
                    f"### [{sev}] `{diag.relative_path}:{diag.line}:{diag.column}`{rule_note}",
                    "",
                    f"{diag.message}",
                    "",
                ])

            if len(report.all_diagnostics) > 100:
                lines.append(f"*... and {len(report.all_diagnostics) - 100} more diagnostics*")
                lines.append("")

        return "\n".join(lines)
