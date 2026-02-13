"""
CLI Command Handlers

This module re-exports all handler functions from the original CLI.
The handlers contain the actual business logic for each command.

In a future refactoring, these can be broken into separate modules:
- quality_handlers.py
- security_handlers.py
- performance_handlers.py
- etc.
"""

# Re-export all handler functions from the original CLI module
# This allows the new modular structure to work while preserving the existing functionality

# Import the original CLI module to access its functions
# We use a lazy import pattern to avoid circular imports
import sys
from pathlib import Path
from typing import TYPE_CHECKING

# These will be populated when first called
_handlers_loaded = False
_handler_functions = {}


def _load_handlers():
    """Load handlers from the original CLI on first use."""
    global _handlers_loaded, _handler_functions
    if _handlers_loaded:
        return

    # Import from the original CLI location (will be moved here eventually)
    # For now, we inline the handler implementations to avoid circular imports
    _handlers_loaded = True


def _create_handler(func_name: str, analysis_func):
    """Create a handler wrapper that loads the original function on first call."""
    def wrapper(*args, **kwargs):
        return analysis_func(*args, **kwargs)
    wrapper.__name__ = func_name
    return wrapper


# Import directly from the original module's namespace
# These functions will be available after the original cli.py is modified
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List

from Asgard.Heimdall.Quality.models.analysis_models import (
    AnalysisConfig,
    AnalysisResult,
    DEFAULT_EXTENSION_THRESHOLDS,
    SeverityLevel,
)
from Asgard.Heimdall.Quality.models.complexity_models import (
    ComplexityConfig,
    ComplexityResult,
    ComplexitySeverity,
)
from Asgard.Heimdall.Quality.models.duplication_models import (
    DuplicationConfig,
    DuplicationResult,
    DuplicationSeverity,
)
from Asgard.Heimdall.Quality.models.smell_models import (
    SmellConfig,
    SmellSeverity,
    SmellThresholds,
)
from Asgard.Heimdall.Quality.models.debt_models import (
    DebtConfig,
    DebtSeverity,
    TimeHorizon,
)
from Asgard.Heimdall.Quality.models.maintainability_models import (
    MaintainabilityConfig,
    MaintainabilityLevel,
    LanguageProfile,
)
from Asgard.Heimdall.Quality.services.file_length_analyzer import FileAnalyzer
from Asgard.Heimdall.Quality.services.complexity_analyzer import ComplexityAnalyzer
from Asgard.Heimdall.Quality.services.duplication_detector import DuplicationDetector
from Asgard.Heimdall.Quality.services.code_smell_detector import CodeSmellDetector
from Asgard.Heimdall.Quality.services.technical_debt_analyzer import TechnicalDebtAnalyzer
from Asgard.Heimdall.Quality.services.maintainability_analyzer import MaintainabilityAnalyzer

from Asgard.Heimdall.Quality.models.env_fallback_models import (
    EnvFallbackConfig,
    EnvFallbackSeverity,
)
from Asgard.Heimdall.Quality.services.env_fallback_scanner import EnvFallbackScanner

from Asgard.Heimdall.Quality.models.lazy_import_models import (
    LazyImportConfig,
    LazyImportSeverity,
)
from Asgard.Heimdall.Quality.services.lazy_import_scanner import LazyImportScanner

from Asgard.Heimdall.Quality.models.library_usage_models import (
    ForbiddenImportConfig,
    ForbiddenImportSeverity,
)
from Asgard.Heimdall.Quality.services.library_usage_scanner import LibraryUsageScanner

from Asgard.Heimdall.Quality.models.datetime_models import (
    DatetimeConfig,
)
from Asgard.Heimdall.Quality.services.datetime_scanner import DatetimeScanner

from Asgard.Heimdall.Quality.models.typing_models import (
    TypingConfig,
)
from Asgard.Heimdall.Quality.services.typing_scanner import TypingScanner

from Asgard.Heimdall.Security.models.security_models import (
    SecurityScanConfig,
    SecuritySeverity,
)
from Asgard.Heimdall.Security.services.static_security_service import StaticSecurityService

from Asgard.Heimdall.Performance.models.performance_models import (
    PerformanceScanConfig,
    PerformanceSeverity,
)
from Asgard.Heimdall.Performance.services.static_performance_service import StaticPerformanceService

from Asgard.Heimdall.OOP.models.oop_models import OOPConfig
from Asgard.Heimdall.OOP.services.oop_analyzer import OOPAnalyzer

from Asgard.Heimdall.Dependencies.models.dependency_models import DependencyConfig
from Asgard.Heimdall.Dependencies.services.dependency_analyzer import DependencyAnalyzer

from Asgard.Heimdall.Architecture.models.architecture_models import ArchitectureConfig
from Asgard.Heimdall.Architecture.services.architecture_analyzer import ArchitectureAnalyzer

from Asgard.Heimdall.Coverage.models.coverage_models import CoverageConfig
from Asgard.Heimdall.Coverage.services.coverage_analyzer import CoverageAnalyzer

from Asgard.Heimdall.Quality.models.syntax_models import (
    LinterType,
    SyntaxConfig,
    SyntaxSeverity,
)
from Asgard.Heimdall.Quality.services.syntax_checker import SyntaxChecker

from Asgard.Heimdall.Dependencies.models.requirements_models import (
    RequirementsConfig,
)
from Asgard.Heimdall.Dependencies.services.requirements_checker import RequirementsChecker

from Asgard.Heimdall.Dependencies.models.license_models import LicenseConfig
from Asgard.Heimdall.Dependencies.services.license_checker import LicenseChecker

from Asgard.Heimdall.cli.common import SEVERITY_MARKERS


def run_quality_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute the file length quality analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    # Check for dry-run mode
    if getattr(args, 'dry_run', False):
        from Asgard.Heimdall.Quality.utilities.file_utils import discover_files
        files = list(discover_files(scan_path, args.exclude if args.exclude else []))
        print(f"\nDry run: Would analyze {len(files)} files")
        for f in sorted(files)[:20]:
            print(f"  {f}")
        if len(files) > 20:
            print(f"  ... and {len(files) - 20} more")
        return 0

    # Build extension thresholds
    ext_thresholds = dict(DEFAULT_EXTENSION_THRESHOLDS)
    if hasattr(args, 'ext_threshold') and args.ext_threshold:
        for et in args.ext_threshold:
            if ":" in et:
                parts = et.split(":")
                ext = parts[0] if parts[0].startswith(".") else f".{parts[0]}"
                try:
                    ext_thresholds[ext] = int(parts[1])
                except ValueError:
                    pass

    # Build exclude patterns
    exclude_patterns = list(args.exclude) if args.exclude else []

    # Build configuration
    config = AnalysisConfig(
        scan_path=scan_path,
        default_threshold=args.threshold if args.threshold else 300,
        extension_thresholds=ext_thresholds,
        include_extensions=args.extensions if hasattr(args, 'extensions') and args.extensions else None,
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        analyzer = FileAnalyzer(config)
        result = analyzer.analyze()

        # Format and print results
        if args.format == "json":
            output = {
                "scan_path": result.scan_path,
                "thresholds": {"default": result.default_threshold, "by_extension": result.extension_thresholds},
                "scanned_at": result.scanned_at.isoformat(),
                "scan_duration_seconds": result.scan_duration_seconds,
                "summary": {
                    "total_files_scanned": result.total_files_scanned,
                    "files_exceeding_threshold": result.files_exceeding_threshold,
                    "compliance_rate": round(result.compliance_rate, 2),
                },
                "violations": [
                    {"file_path": v.relative_path, "line_count": v.line_count, "threshold": v.threshold,
                     "lines_over": v.lines_over, "severity": v.severity, "extension": v.file_extension}
                    for v in result.violations
                ],
            }
            print(json.dumps(output, indent=2))
        else:
            # Text format
            lines = [
                "", "=" * 70, "  HEIMDALL CODE QUALITY REPORT", "  File Length Analysis", "=" * 70, "",
                f"  Scan Path:    {result.scan_path}",
                f"  Scanned At:   {result.scanned_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"  Duration:     {result.scan_duration_seconds:.2f}s", ""
            ]

            if result.has_violations:
                lines.extend(["-" * 70, "  FILES EXCEEDING THRESHOLD", "-" * 70, ""])
                by_severity = result.get_violations_by_severity()
                for severity in [SeverityLevel.CRITICAL.value, SeverityLevel.SEVERE.value,
                                 SeverityLevel.MODERATE.value, SeverityLevel.WARNING.value]:
                    violations = by_severity[severity]
                    if violations:
                        lines.append(f"  {SEVERITY_MARKERS[severity]}")
                        lines.append("")
                        for v in violations:
                            lines.append(f"    {v.relative_path}")
                            lines.append(f"      {v.line_count} lines (+{v.lines_over} over {v.threshold}-line threshold)")
                            lines.append("")
            else:
                lines.extend(["  All files are within the threshold. Nice work!", ""])

            lines.extend(["-" * 70, "  SUMMARY", "-" * 70, "",
                          f"  Files Scanned:          {result.total_files_scanned}",
                          f"  Files Over Threshold:   {result.files_exceeding_threshold}",
                          f"  Compliance Rate:        {result.compliance_rate:.1f}%", "",
                          "=" * 70, ""])
            print("\n".join(lines))

        return 1 if result.has_violations else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_complexity_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute the complexity analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    config = ComplexityConfig(
        scan_path=scan_path,
        cyclomatic_threshold=args.cyclomatic_threshold,
        cognitive_threshold=args.cognitive_threshold,
        include_tests=getattr(args, 'include_tests', False),
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        analyzer = ComplexityAnalyzer(config)
        result = analyzer.analyze()
        report = analyzer.generate_report(result, args.format)
        print(report)
        return 1 if result.has_violations else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_duplication_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute the duplication analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    config = DuplicationConfig(
        scan_path=scan_path,
        min_block_size=getattr(args, 'min_lines', 6),
        similarity_threshold=getattr(args, 'min_tokens', 50) / 100.0,
        output_format=args.format,
        include_tests=getattr(args, 'include_tests', False),
        exclude_patterns=exclude_patterns,
        verbose=verbose,
    )

    try:
        detector = DuplicationDetector(config)
        result = detector.analyze()
        report = detector.generate_report(result, args.format)
        print(report)
        return 1 if result.has_duplicates else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_smell_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute the code smell analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    thresholds = SmellThresholds(
        long_method_lines=getattr(args, 'long_method_lines', 50),
        large_class_methods=getattr(args, 'large_class_methods', 20),
        long_parameter_list=getattr(args, 'long_parameter_list', 5),
    )

    config = SmellConfig(
        scan_path=scan_path,
        smell_categories=getattr(args, 'categories', None),
        severity_filter=SmellSeverity(args.severity),
        thresholds=thresholds,
        output_format=args.format,
        include_tests=getattr(args, 'include_tests', False),
        exclude_patterns=exclude_patterns,
        verbose=verbose,
    )

    try:
        detector = CodeSmellDetector(config)
        result = detector.analyze(scan_path)
        report = detector.generate_report(result, args.format)
        print(report)
        return 1 if result.has_smells else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_debt_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute the technical debt analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    config = DebtConfig(
        scan_path=scan_path,
        debt_types=getattr(args, 'debt_types', None),
        time_horizon=TimeHorizon(getattr(args, 'time_horizon', 'all')),
        include_tests=getattr(args, 'include_tests', False),
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        analyzer = TechnicalDebtAnalyzer(config)
        result = analyzer.analyze(scan_path)
        report = analyzer.generate_report(result, args.format)
        print(report)
        return 1 if result.has_debt else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_maintainability_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute the maintainability index analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    config = MaintainabilityConfig(
        scan_path=scan_path,
        include_halstead=not getattr(args, 'no_halstead', False),
        include_comments=not getattr(args, 'no_comments', False),
        language_profile=LanguageProfile(getattr(args, 'language', 'python')),
        include_tests=getattr(args, 'include_tests', False),
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        analyzer = MaintainabilityAnalyzer(config)
        result = analyzer.analyze(scan_path)
        report = analyzer.generate_report(result, args.format)
        print(report)
        return 1 if result.has_issues else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_env_fallback_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute the environment variable fallback analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    severity_map = {
        "low": EnvFallbackSeverity.LOW,
        "medium": EnvFallbackSeverity.MEDIUM,
        "high": EnvFallbackSeverity.HIGH,
    }
    severity_filter = severity_map.get(args.severity, EnvFallbackSeverity.LOW)

    config = EnvFallbackConfig(
        scan_path=scan_path,
        severity_filter=severity_filter,
        include_tests=getattr(args, 'include_tests', False),
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        scanner = EnvFallbackScanner(config)
        result = scanner.analyze(scan_path)
        report = scanner.generate_report(result, args.format)
        print(report)
        return 1 if result.has_violations else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_lazy_imports_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute the lazy imports analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    severity_map = {
        "low": LazyImportSeverity.LOW,
        "medium": LazyImportSeverity.MEDIUM,
        "high": LazyImportSeverity.HIGH,
    }
    severity_filter = severity_map.get(args.severity, LazyImportSeverity.LOW)

    config = LazyImportConfig(
        scan_path=scan_path,
        severity_filter=severity_filter,
        include_tests=getattr(args, 'include_tests', False),
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        scanner = LazyImportScanner(config)
        result = scanner.analyze(scan_path)
        report = scanner.generate_report(result, args.format)
        print(report)
        return 1 if result.has_violations else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_security_analysis(args: argparse.Namespace, verbose: bool = False, analysis_type: str = "all") -> int:
    """Execute security analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    severity_map = {
        "info": SecuritySeverity.INFO,
        "low": SecuritySeverity.LOW,
        "medium": SecuritySeverity.MEDIUM,
        "high": SecuritySeverity.HIGH,
        "critical": SecuritySeverity.CRITICAL,
    }
    min_severity = severity_map.get(args.severity, SecuritySeverity.LOW)

    config = SecurityScanConfig(
        scan_path=scan_path,
        scan_type=analysis_type,
        min_severity=min_severity,
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        service = StaticSecurityService(config)
        result = service.analyze(scan_path)
        report = service.generate_report(result, args.format)
        print(report)
        return 1 if result.has_vulnerabilities else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_performance_analysis(args: argparse.Namespace, verbose: bool = False, analysis_type: str = "all") -> int:
    """Execute performance analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    severity_map = {
        "info": PerformanceSeverity.INFO,
        "low": PerformanceSeverity.LOW,
        "medium": PerformanceSeverity.MEDIUM,
        "high": PerformanceSeverity.HIGH,
        "critical": PerformanceSeverity.CRITICAL,
    }
    min_severity = severity_map.get(args.severity, PerformanceSeverity.LOW)

    config = PerformanceScanConfig(
        scan_path=scan_path,
        scan_type=analysis_type,
        min_severity=min_severity,
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        service = StaticPerformanceService(config)
        result = service.analyze(scan_path)
        report = service.generate_report(result, args.format)
        print(report)
        return 1 if result.has_issues else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_oop_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute OOP metrics analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    config = OOPConfig(
        scan_path=scan_path,
        cbo_threshold=args.cbo_threshold,
        lcom_threshold=args.lcom_threshold,
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        analyzer = OOPAnalyzer(config)
        result = analyzer.analyze(scan_path)
        report = analyzer.generate_report(result, args.format)
        print(report)
        return 1 if result.has_issues else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_deps_analysis(args: argparse.Namespace, verbose: bool = False, analysis_type: str = "all") -> int:
    """Execute dependency analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    config = DependencyConfig(
        scan_path=scan_path,
        max_depth=getattr(args, 'max_depth', 10),
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        analyzer = DependencyAnalyzer(config)

        if analysis_type == "cycles":
            result = analyzer.find_cycles(scan_path)
            report = analyzer.generate_cycles_report(result, args.format)
            print(report)
            return 1 if result else 0
        elif analysis_type == "modularity":
            result = analyzer.analyze_modularity(scan_path)
            report = analyzer.generate_modularity_report(result, args.format)
            print(report)
            return 1 if result.has_issues else 0
        else:
            result = analyzer.analyze(scan_path)
            report = analyzer.generate_report(result, args.format)
            print(report)
            return 1 if result.has_issues else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_arch_analysis(args: argparse.Namespace, verbose: bool = False, analysis_type: str = "all") -> int:
    """Execute architecture analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    config = ArchitectureConfig(
        scan_path=scan_path,
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        analyzer = ArchitectureAnalyzer(config)

        validate_solid = not getattr(args, 'no_solid', False) if analysis_type == "all" else analysis_type == "solid"
        analyze_layers = not getattr(args, 'no_layers', False) if analysis_type == "all" else analysis_type == "layers"
        detect_patterns = not getattr(args, 'no_patterns', False) if analysis_type == "all" else analysis_type == "patterns"

        result = analyzer.analyze(
            scan_path,
            validate_solid=validate_solid,
            analyze_layers=analyze_layers,
            detect_patterns=detect_patterns
        )
        report = analyzer.generate_report(result, args.format)
        print(report)
        return 1 if not result.is_healthy else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_coverage_analysis(args: argparse.Namespace, verbose: bool = False, analysis_type: str = "all") -> int:
    """Execute coverage analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    test_path = None
    if hasattr(args, 'test_path') and args.test_path:
        test_path = Path(args.test_path).resolve()

    config = CoverageConfig(
        scan_path=scan_path,
        include_private=getattr(args, 'include_private', False),
        exclude_patterns=exclude_patterns,
    )

    try:
        analyzer = CoverageAnalyzer(config)

        if analysis_type == "gaps":
            gaps = analyzer.get_gaps(scan_path)
            if args.format == "json":
                print(json.dumps([{
                    "method": g.method.full_name,
                    "file": g.file_path,
                    "severity": g.severity.value,
                    "message": g.message,
                } for g in gaps], indent=2))
            else:
                print(f"\nCoverage Gaps Found: {len(gaps)}")
                for g in gaps[:20]:
                    print(f"  [{g.severity.value.upper()}] {g.method.full_name}")
                if len(gaps) > 20:
                    print(f"  ... and {len(gaps) - 20} more")
            return 1 if gaps else 0
        elif analysis_type == "suggestions":
            max_suggestions = getattr(args, 'max_suggestions', 10)
            suggestions = analyzer.get_suggestions(scan_path, max_suggestions)
            if args.format == "json":
                print(json.dumps([{
                    "test_name": s.test_name,
                    "method": s.method.full_name,
                    "priority": s.priority.value,
                    "description": s.description,
                } for s in suggestions], indent=2))
            else:
                print(f"\nTest Suggestions ({len(suggestions)}):")
                for s in suggestions:
                    print(f"  [{s.priority.value.upper()}] {s.test_name}")
                    print(f"    {s.description}")
            return 0
        else:
            result = analyzer.analyze(scan_path, test_path)
            report = analyzer.generate_report(result, args.format)
            print(report)
            return 1 if result.has_gaps else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_syntax_analysis(args: argparse.Namespace, verbose: bool = False, fix_mode: bool = False) -> int:
    """Execute syntax checking analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = [
        "__pycache__", ".git", ".venv", "venv", "node_modules",
        ".mypy_cache", ".pytest_cache", "*.egg-info", "build", "dist",
    ]
    if args.exclude:
        exclude_patterns.extend(args.exclude)

    linter_map = {
        "ruff": LinterType.RUFF,
        "flake8": LinterType.FLAKE8,
        "pylint": LinterType.PYLINT,
        "mypy": LinterType.MYPY,
    }
    linters = [linter_map[l] for l in args.linters if l in linter_map]

    severity_map = {
        "error": SyntaxSeverity.ERROR,
        "warning": SyntaxSeverity.WARNING,
        "info": SyntaxSeverity.INFO,
        "style": SyntaxSeverity.STYLE,
    }
    min_severity = severity_map.get(args.severity, SyntaxSeverity.WARNING)

    config = SyntaxConfig(
        scan_path=scan_path,
        include_extensions=args.extensions,
        exclude_patterns=exclude_patterns,
        linters=linters,
        min_severity=min_severity,
        include_style=getattr(args, 'include_style', False),
        fix_mode=fix_mode,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        checker = SyntaxChecker(config)

        if fix_mode:
            result, fixes_applied = checker.fix()
            report = checker.generate_report(result, args.format)
            print(report)
            if fixes_applied > 0:
                print(f"\nApplied {fixes_applied} auto-fixes.")
            return 1 if result.has_errors else 0
        else:
            result = checker.analyze()
            report = checker.generate_report(result, args.format)
            print(report)
            return 1 if result.has_errors else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_requirements_analysis(args: argparse.Namespace, verbose: bool = False, sync_mode: bool = False) -> int:
    """Execute requirements checking analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = [
        "__pycache__", ".git", ".venv", "venv", "node_modules",
        ".pytest_cache", ".mypy_cache", "dist", "build",
        "*.egg-info", "Hercules",
    ]
    if args.exclude:
        exclude_patterns.extend(args.exclude)

    check_unused = getattr(args, "check_unused", True)
    if getattr(args, "no_check_unused", False):
        check_unused = False

    config = RequirementsConfig(
        scan_path=scan_path,
        requirements_files=getattr(args, "requirements_files", ["requirements.txt"]),
        exclude_patterns=exclude_patterns,
        check_unused=check_unused,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        checker = RequirementsChecker(config)

        if sync_mode:
            result, changes = checker.sync(
                target_file=getattr(args, 'target_file', 'requirements.txt')
            )
            report = checker.generate_report(result, args.format)
            print(report)
            if changes:
                print(f"\nSync complete: {len(changes)} changes made")
            return 1 if result.has_issues else 0
        else:
            result = checker.analyze()
            report = checker.generate_report(result, args.format)
            print(report)
            return 1 if result.has_issues else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_licenses_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute license checking analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    config = LicenseConfig(
        scan_path=scan_path,
        requirements_files=getattr(args, "requirements_files", ["requirements.txt"]),
        allowed_licenses=getattr(args, "allowed", None),
        prohibited_licenses=getattr(args, "prohibited", None),
        warning_licenses=getattr(args, "warn", None),
        use_cache=not getattr(args, "no_cache", False),
        output_format=args.format,
        verbose=verbose,
    )

    try:
        checker = LicenseChecker(config)
        result = checker.analyze()
        report = checker.generate_report(result, args.format)
        print(report)
        return 1 if result.has_issues else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_logic_analysis(args: argparse.Namespace, verbose: bool = False, analysis_type: str = "audit") -> int:
    """Execute logic analysis (duplication, patterns, complexity)."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []
    issues_found = False

    if analysis_type in ("duplication", "audit"):
        # Run duplication detection
        config = DuplicationConfig(
            scan_path=scan_path,
            min_block_size=getattr(args, 'min_similarity', 0.8) * 10,
            similarity_threshold=getattr(args, 'min_similarity', 0.8),
            output_format=args.format,
            exclude_patterns=exclude_patterns,
            verbose=verbose,
        )
        try:
            detector = DuplicationDetector(config)
            result = detector.analyze()
            if analysis_type == "duplication":
                report = detector.generate_report(result, args.format)
                print(report)
            else:
                print(f"\n[Duplication] Found {result.total_clone_families} clone families")
            if result.has_duplicates:
                issues_found = True
        except Exception as e:
            print(f"Duplication analysis error: {e}")

    if analysis_type in ("patterns", "audit"):
        # Run code smell detection
        config = SmellConfig(
            scan_path=scan_path,
            severity_filter=SmellSeverity(args.severity),
            output_format=args.format,
            exclude_patterns=exclude_patterns,
            verbose=verbose,
        )
        try:
            detector = CodeSmellDetector(config)
            result = detector.analyze(scan_path)
            if analysis_type == "patterns":
                report = detector.generate_report(result, args.format)
                print(report)
            else:
                print(f"[Patterns] Found {result.total_smells} code smells")
            if result.has_smells:
                issues_found = True
        except Exception as e:
            print(f"Pattern analysis error: {e}")

    if analysis_type in ("complexity", "audit"):
        # Run complexity analysis
        config = ComplexityConfig(
            scan_path=scan_path,
            cyclomatic_threshold=10,
            cognitive_threshold=15,
            output_format=args.format,
            exclude_patterns=exclude_patterns,
            verbose=verbose,
        )
        try:
            analyzer = ComplexityAnalyzer(config)
            result = analyzer.analyze()
            if analysis_type == "complexity":
                report = analyzer.generate_report(result, args.format)
                print(report)
            else:
                print(f"[Complexity] Found {result.total_violations} violations")
            if result.has_violations:
                issues_found = True
        except Exception as e:
            print(f"Complexity analysis error: {e}")

    return 1 if issues_found else 0


def run_forbidden_imports_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute the forbidden imports analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    config = ForbiddenImportConfig(
        scan_path=scan_path,
        include_tests=getattr(args, 'include_tests', False),
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        scanner = LibraryUsageScanner(config)
        result = scanner.analyze(scan_path)
        report = scanner.generate_report(result, args.format)
        print(report)
        return 1 if result.has_violations else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_datetime_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute the datetime usage analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    config = DatetimeConfig(
        scan_path=scan_path,
        check_utcnow=not getattr(args, 'no_check_utcnow', False),
        check_now_no_tz=not getattr(args, 'no_check_now', False),
        check_today_no_tz=not getattr(args, 'no_check_today', False),
        include_tests=getattr(args, 'include_tests', False),
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        scanner = DatetimeScanner(config)
        result = scanner.analyze(scan_path)
        report = scanner.generate_report(result, args.format)
        print(report)
        return 1 if result.has_violations else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_typing_analysis(args: argparse.Namespace, verbose: bool = False) -> int:
    """Execute the typing coverage analysis."""
    scan_path = Path(args.path).resolve()

    if not scan_path.exists():
        print(f"Error: Path does not exist: {scan_path}")
        return 1

    exclude_patterns = list(args.exclude) if args.exclude else []

    config = TypingConfig(
        scan_path=scan_path,
        minimum_coverage=getattr(args, 'threshold', 80.0),
        exclude_private=not getattr(args, 'include_private', False),
        exclude_dunder=not getattr(args, 'include_dunder', False),
        include_tests=getattr(args, 'include_tests', False),
        exclude_patterns=exclude_patterns,
        output_format=args.format,
        verbose=verbose,
    )

    try:
        scanner = TypingScanner(config)
        result = scanner.analyze(scan_path)
        report = scanner.generate_report(result, args.format)
        print(report)
        return 1 if result.has_violations else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


__all__ = [
    "run_quality_analysis",
    "run_complexity_analysis",
    "run_duplication_analysis",
    "run_smell_analysis",
    "run_debt_analysis",
    "run_maintainability_analysis",
    "run_env_fallback_analysis",
    "run_lazy_imports_analysis",
    "run_security_analysis",
    "run_performance_analysis",
    "run_oop_analysis",
    "run_deps_analysis",
    "run_arch_analysis",
    "run_coverage_analysis",
    "run_syntax_analysis",
    "run_requirements_analysis",
    "run_licenses_analysis",
    "run_logic_analysis",
]
