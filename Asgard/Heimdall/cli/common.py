"""
Common utilities shared across all CLI modules.

Contains severity markers, shared argument helpers, and utility functions.
"""

import argparse

from Asgard.Heimdall.Quality.models.analysis_models import SeverityLevel
from Asgard.Heimdall.Quality.models.complexity_models import ComplexitySeverity
from Asgard.Heimdall.Quality.models.duplication_models import DuplicationSeverity
from Asgard.Heimdall.Quality.models.smell_models import SmellSeverity
from Asgard.Heimdall.Quality.models.debt_models import DebtSeverity
from Asgard.Heimdall.Quality.models.maintainability_models import MaintainabilityLevel
from Asgard.Heimdall.Quality.models.env_fallback_models import EnvFallbackSeverity
from Asgard.Heimdall.Quality.models.lazy_import_models import LazyImportSeverity
from Asgard.Heimdall.Quality.models.syntax_models import SyntaxSeverity
from Asgard.Heimdall.Quality.models.library_usage_models import ForbiddenImportSeverity
from Asgard.Heimdall.Quality.models.datetime_models import DatetimeSeverity
from Asgard.Heimdall.Quality.models.typing_models import AnnotationSeverity
from Asgard.Heimdall.Security.models.security_models import SecuritySeverity
from Asgard.Heimdall.Performance.models.performance_models import PerformanceSeverity

# Severity display markers for terminal output
SEVERITY_MARKERS = {
    SeverityLevel.CRITICAL.value: "[CRITICAL]",
    SeverityLevel.SEVERE.value: "[SEVERE]",
    SeverityLevel.MODERATE.value: "[MODERATE]",
    SeverityLevel.WARNING.value: "[WARNING]",
}

COMPLEXITY_SEVERITY_MARKERS = {
    ComplexitySeverity.CRITICAL.value: "[CRITICAL]",
    ComplexitySeverity.VERY_HIGH.value: "[VERY HIGH]",
    ComplexitySeverity.HIGH.value: "[HIGH]",
    ComplexitySeverity.MODERATE.value: "[MODERATE]",
    ComplexitySeverity.LOW.value: "[LOW]",
}

DUPLICATION_SEVERITY_MARKERS = {
    DuplicationSeverity.CRITICAL.value: "[CRITICAL]",
    DuplicationSeverity.HIGH.value: "[HIGH]",
    DuplicationSeverity.MODERATE.value: "[MODERATE]",
    DuplicationSeverity.LOW.value: "[LOW]",
}

SMELL_SEVERITY_MARKERS = {
    SmellSeverity.CRITICAL.value: "[CRITICAL]",
    SmellSeverity.HIGH.value: "[HIGH]",
    SmellSeverity.MEDIUM.value: "[MEDIUM]",
    SmellSeverity.LOW.value: "[LOW]",
}

DEBT_SEVERITY_MARKERS = {
    DebtSeverity.CRITICAL.value: "[CRITICAL]",
    DebtSeverity.HIGH.value: "[HIGH]",
    DebtSeverity.MEDIUM.value: "[MEDIUM]",
    DebtSeverity.LOW.value: "[LOW]",
}

MAINTAINABILITY_LEVEL_MARKERS = {
    MaintainabilityLevel.EXCELLENT.value: "[EXCELLENT]",
    MaintainabilityLevel.GOOD.value: "[GOOD]",
    MaintainabilityLevel.MODERATE.value: "[MODERATE]",
    MaintainabilityLevel.POOR.value: "[POOR]",
    MaintainabilityLevel.CRITICAL.value: "[CRITICAL]",
}

ENV_FALLBACK_SEVERITY_MARKERS = {
    EnvFallbackSeverity.HIGH.value: "[HIGH]",
    EnvFallbackSeverity.MEDIUM.value: "[MEDIUM]",
    EnvFallbackSeverity.LOW.value: "[LOW]",
}

LAZY_IMPORT_SEVERITY_MARKERS = {
    LazyImportSeverity.HIGH.value: "[HIGH]",
    LazyImportSeverity.MEDIUM.value: "[MEDIUM]",
    LazyImportSeverity.LOW.value: "[LOW]",
}

FORBIDDEN_IMPORT_SEVERITY_MARKERS = {
    ForbiddenImportSeverity.HIGH.value: "[HIGH]",
    ForbiddenImportSeverity.MEDIUM.value: "[MEDIUM]",
    ForbiddenImportSeverity.LOW.value: "[LOW]",
}

DATETIME_SEVERITY_MARKERS = {
    DatetimeSeverity.HIGH.value: "[HIGH]",
    DatetimeSeverity.MEDIUM.value: "[MEDIUM]",
    DatetimeSeverity.LOW.value: "[LOW]",
}

TYPING_SEVERITY_MARKERS = {
    AnnotationSeverity.HIGH.value: "[HIGH]",
    AnnotationSeverity.MEDIUM.value: "[MEDIUM]",
    AnnotationSeverity.LOW.value: "[LOW]",
}

SYNTAX_SEVERITY_MARKERS = {
    SyntaxSeverity.ERROR.value: "[ERROR]",
    SyntaxSeverity.WARNING.value: "[WARNING]",
    SyntaxSeverity.INFO.value: "[INFO]",
    SyntaxSeverity.STYLE.value: "[STYLE]",
}

SECURITY_SEVERITY_MARKERS = {
    SecuritySeverity.CRITICAL.value: "[CRITICAL]",
    SecuritySeverity.HIGH.value: "[HIGH]",
    SecuritySeverity.MEDIUM.value: "[MEDIUM]",
    SecuritySeverity.LOW.value: "[LOW]",
    SecuritySeverity.INFO.value: "[INFO]",
}

PERFORMANCE_SEVERITY_MARKERS = {
    PerformanceSeverity.CRITICAL.value: "[CRITICAL]",
    PerformanceSeverity.HIGH.value: "[HIGH]",
    PerformanceSeverity.MEDIUM.value: "[MEDIUM]",
    PerformanceSeverity.LOW.value: "[LOW]",
    PerformanceSeverity.INFO.value: "[INFO]",
}


def add_performance_flags(parser: argparse.ArgumentParser) -> None:
    """Add performance-related flags to a parser (parallel, incremental, cache)."""
    parser.add_argument(
        "--parallel",
        "-P",
        action="store_true",
        help="Enable parallel processing for faster analysis",
    )
    parser.add_argument(
        "--workers",
        "-W",
        type=int,
        default=None,
        help="Number of worker processes (default: CPU count - 1)",
    )
    parser.add_argument(
        "--incremental",
        "-I",
        action="store_true",
        help="Enable incremental scanning (skip unchanged files)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching even if incremental mode is enabled",
    )
    parser.add_argument(
        "--baseline",
        "-B",
        type=str,
        default=None,
        help="Path to baseline file for filtering known issues",
    )


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to a parser (path, format, thresholds, dry-run, exclude)."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown", "github"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--threshold",
        "-t",
        type=int,
        default=None,
        help="Line threshold (default: varies by file type)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="List files that would be scanned without analyzing",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )
    # Add performance flags to common args
    add_performance_flags(parser)


def add_complexity_args(parser: argparse.ArgumentParser) -> None:
    """Add complexity analysis arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--cyclomatic-threshold",
        "-c",
        type=int,
        default=10,
        help="Cyclomatic complexity threshold (default: 10)",
    )
    parser.add_argument(
        "--cognitive-threshold",
        "-g",
        type=int,
        default=15,
        help="Cognitive complexity threshold (default: 15)",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_duplication_args(parser: argparse.ArgumentParser) -> None:
    """Add duplication detection arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--min-lines",
        "-l",
        type=int,
        default=6,
        help="Minimum lines for a duplicate (default: 6)",
    )
    parser.add_argument(
        "--min-tokens",
        "-k",
        type=int,
        default=50,
        help="Minimum tokens for a duplicate (default: 50)",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_smell_args(parser: argparse.ArgumentParser) -> None:
    """Add code smell detection arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--severity",
        "-s",
        choices=["low", "medium", "high", "critical"],
        default="low",
        help="Minimum severity to report (default: low)",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_debt_args(parser: argparse.ArgumentParser) -> None:
    """Add technical debt analysis arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--severity",
        "-s",
        choices=["low", "medium", "high", "critical"],
        default="low",
        help="Minimum severity to report (default: low)",
    )
    parser.add_argument(
        "--horizon",
        "-H",
        choices=["immediate", "short", "medium", "long"],
        default=None,
        help="Filter by time horizon",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_maintainability_args(parser: argparse.ArgumentParser) -> None:
    """Add maintainability analysis arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in analysis",
    )


def add_env_fallback_args(parser: argparse.ArgumentParser) -> None:
    """Add environment fallback scanner arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--severity",
        "-s",
        choices=["low", "medium", "high"],
        default="low",
        help="Minimum severity to report (default: low)",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in analysis",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_lazy_imports_args(parser: argparse.ArgumentParser) -> None:
    """Add lazy imports scanner arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--severity",
        "-s",
        choices=["low", "medium", "high"],
        default="low",
        help="Minimum severity to report (default: low)",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in analysis",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_security_args(parser: argparse.ArgumentParser) -> None:
    """Add security analysis arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--severity",
        "-s",
        choices=["info", "low", "medium", "high", "critical"],
        default="low",
        help="Minimum severity to report (default: low)",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_performance_args(parser: argparse.ArgumentParser) -> None:
    """Add performance analysis arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--severity",
        "-s",
        choices=["info", "low", "medium", "high", "critical"],
        default="low",
        help="Minimum severity to report (default: low)",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_oop_args(parser: argparse.ArgumentParser) -> None:
    """Add OOP analysis arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--cbo-threshold",
        type=int,
        default=14,
        help="CBO threshold for high coupling (default: 14)",
    )
    parser.add_argument(
        "--lcom-threshold",
        type=float,
        default=0.8,
        help="LCOM threshold for poor cohesion (default: 0.8)",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_deps_args(parser: argparse.ArgumentParser) -> None:
    """Add dependency analysis arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Maximum depth for dependency graph (default: 10)",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_arch_args(parser: argparse.ArgumentParser) -> None:
    """Add architecture analysis arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--no-solid",
        action="store_true",
        help="Skip SOLID principle validation",
    )
    parser.add_argument(
        "--no-layers",
        action="store_true",
        help="Skip layer analysis",
    )
    parser.add_argument(
        "--no-patterns",
        action="store_true",
        help="Skip design pattern detection",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_coverage_args(parser: argparse.ArgumentParser) -> None:
    """Add coverage analysis arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--test-path",
        type=str,
        default=None,
        help="Path to test directory",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="Include private methods in analysis",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )
    parser.add_argument(
        "--max-suggestions",
        type=int,
        default=10,
        help="Maximum number of test suggestions (default: 10)",
    )


def add_syntax_args(parser: argparse.ArgumentParser) -> None:
    """Add syntax checking arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--linters",
        nargs="+",
        choices=["ruff", "flake8", "pylint", "mypy"],
        default=["ruff"],
        help="Linters to use (default: ruff)",
    )
    parser.add_argument(
        "--severity",
        "-s",
        choices=["error", "warning", "info", "style"],
        default="warning",
        help="Minimum severity to report (default: warning)",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=[".py"],
        help="File extensions to check (default: .py)",
    )
    parser.add_argument(
        "--include-style",
        action="store_true",
        help="Include style issues in output",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_requirements_args(parser: argparse.ArgumentParser) -> None:
    """Add requirements checking arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--requirements-files",
        nargs="+",
        default=["requirements.txt"],
        help="Requirements files to check (default: requirements.txt)",
    )
    parser.add_argument(
        "--no-check-unused",
        action="store_true",
        help="Skip checking for unused requirements",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_licenses_args(parser: argparse.ArgumentParser) -> None:
    """Add license checking arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--allowed",
        nargs="+",
        default=None,
        help="Allowed license types",
    )
    parser.add_argument(
        "--denied",
        nargs="+",
        default=None,
        help="Denied license types",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_logic_args(parser: argparse.ArgumentParser) -> None:
    """Add logic analysis arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--severity",
        "-s",
        choices=["low", "medium", "high", "critical"],
        default="low",
        help="Minimum severity to report (default: low)",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_forbidden_imports_args(parser: argparse.ArgumentParser) -> None:
    """Add forbidden imports scanner arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in analysis",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_datetime_args(parser: argparse.ArgumentParser) -> None:
    """Add datetime scanner arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--no-check-utcnow",
        action="store_true",
        help="Skip checking for datetime.utcnow()",
    )
    parser.add_argument(
        "--no-check-now",
        action="store_true",
        help="Skip checking for datetime.now() without timezone",
    )
    parser.add_argument(
        "--no-check-today",
        action="store_true",
        help="Skip checking for datetime.today()",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in analysis",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )


def add_typing_args(parser: argparse.ArgumentParser) -> None:
    """Add typing coverage scanner arguments to a parser."""
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=80.0,
        help="Minimum typing coverage percentage (default: 80.0)",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="Include private methods (_method) in analysis",
    )
    parser.add_argument(
        "--include-dunder",
        action="store_true",
        help="Include dunder methods (__method__) in analysis",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files in analysis",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="+",
        default=[],
        help="Additional patterns to exclude",
    )
