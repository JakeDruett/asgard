"""
Heimdall CLI Main Entry Point

This module provides the main CLI entry point and parser creation.
Command handlers are delegated to submodules for better organization.
"""

import argparse
import sys

from Asgard.Heimdall.cli.common import (
    add_common_args,
    add_complexity_args,
    add_duplication_args,
    add_smell_args,
    add_debt_args,
    add_maintainability_args,
    add_env_fallback_args,
    add_lazy_imports_args,
    add_forbidden_imports_args,
    add_datetime_args,
    add_typing_args,
    add_security_args,
    add_performance_args,
    add_oop_args,
    add_deps_args,
    add_arch_args,
    add_coverage_args,
    add_syntax_args,
    add_requirements_args,
    add_licenses_args,
    add_logic_args,
)

# Import handlers from the original CLI (will be refactored into separate modules)
from Asgard.Heimdall.cli.handlers import (
    run_quality_analysis,
    run_complexity_analysis,
    run_duplication_analysis,
    run_smell_analysis,
    run_debt_analysis,
    run_maintainability_analysis,
    run_env_fallback_analysis,
    run_lazy_imports_analysis,
    run_forbidden_imports_analysis,
    run_datetime_analysis,
    run_typing_analysis,
    run_security_analysis,
    run_performance_analysis,
    run_oop_analysis,
    run_deps_analysis,
    run_arch_analysis,
    run_coverage_analysis,
    run_syntax_analysis,
    run_requirements_analysis,
    run_licenses_analysis,
    run_logic_analysis,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="heimdall",
        description="Heimdall - Code Quality Control for GAIA",
        epilog="Named after the Norse watchman god who guards Bifrost and sees all.",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output showing all scanned files",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Heimdall 1.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Quality command group
    _setup_quality_commands(subparsers)

    # Audit command (alias for quality analyze)
    audit_parser = subparsers.add_parser("audit", help="Run all quality checks (alias for 'quality analyze')")
    add_common_args(audit_parser)

    # Security command group
    _setup_security_commands(subparsers)

    # Performance command group
    _setup_performance_commands(subparsers)

    # OOP command group
    _setup_oop_commands(subparsers)

    # Dependencies command group
    _setup_deps_commands(subparsers)

    # Architecture command group
    _setup_arch_commands(subparsers)

    # Coverage command group
    _setup_coverage_commands(subparsers)

    # Syntax command group
    _setup_syntax_commands(subparsers)

    # Requirements command group
    _setup_requirements_commands(subparsers)

    # Licenses command group
    _setup_licenses_commands(subparsers)

    # Logic command group
    _setup_logic_commands(subparsers)

    return parser


def _setup_quality_commands(subparsers) -> None:
    """Set up quality command group."""
    quality_parser = subparsers.add_parser("quality", help="Code quality analysis")
    quality_subparsers = quality_parser.add_subparsers(dest="quality_command", help="Quality commands")

    # Quality analyze (all quality checks)
    quality_analyze = quality_subparsers.add_parser("analyze", help="Run all quality checks")
    add_common_args(quality_analyze)

    # Quality file-length
    quality_file_length = quality_subparsers.add_parser("file-length", help="Check file lengths only")
    add_common_args(quality_file_length)

    # Quality complexity
    quality_complexity = quality_subparsers.add_parser("complexity", help="Analyze code complexity")
    add_complexity_args(quality_complexity)

    # Quality duplication
    quality_duplication = quality_subparsers.add_parser("duplication", help="Detect code duplication")
    add_duplication_args(quality_duplication)

    # Quality smells
    quality_smells = quality_subparsers.add_parser("smells", help="Detect code smells")
    add_smell_args(quality_smells)

    # Quality debt
    quality_debt = quality_subparsers.add_parser("debt", help="Analyze technical debt")
    add_debt_args(quality_debt)

    # Quality maintainability
    quality_maintainability = quality_subparsers.add_parser("maintainability", help="Analyze maintainability index")
    add_maintainability_args(quality_maintainability)

    # Quality env-fallback
    quality_env_fallback = quality_subparsers.add_parser(
        "env-fallback",
        help="Detect default/fallback values in environment variable access"
    )
    add_env_fallback_args(quality_env_fallback)

    # Quality lazy-imports
    quality_lazy_imports = quality_subparsers.add_parser(
        "lazy-imports",
        help="Detect imports not at module level (inside functions, methods, etc.)"
    )
    add_lazy_imports_args(quality_lazy_imports)

    # Quality forbidden-imports
    quality_forbidden_imports = quality_subparsers.add_parser(
        "forbidden-imports",
        help="Detect imports of forbidden libraries that should use wrappers"
    )
    add_forbidden_imports_args(quality_forbidden_imports)

    # Quality datetime
    quality_datetime = quality_subparsers.add_parser(
        "datetime",
        help="Detect deprecated and unsafe datetime usage patterns"
    )
    add_datetime_args(quality_datetime)

    # Quality typing
    quality_typing = quality_subparsers.add_parser(
        "typing",
        help="Analyze type annotation coverage"
    )
    add_typing_args(quality_typing)


def _setup_security_commands(subparsers) -> None:
    """Set up security command group."""
    security_parser = subparsers.add_parser("security", help="Security vulnerability analysis")
    security_subparsers = security_parser.add_subparsers(dest="security_command", help="Security commands")

    for cmd, desc in [
        ("scan", "Run all security checks"),
        ("secrets", "Detect hardcoded secrets"),
        ("dependencies", "Scan for vulnerable dependencies"),
        ("vulnerabilities", "Detect injection vulnerabilities"),
        ("crypto", "Validate cryptographic implementations"),
        ("access", "Analyze access control issues"),
        ("auth", "Analyze authentication issues"),
        ("headers", "Analyze security headers"),
        ("tls", "Analyze TLS/SSL configuration"),
        ("container", "Analyze container security"),
        ("infra", "Analyze infrastructure security"),
    ]:
        sub = security_subparsers.add_parser(cmd, help=desc)
        add_security_args(sub)


def _setup_performance_commands(subparsers) -> None:
    """Set up performance command group."""
    performance_parser = subparsers.add_parser("performance", help="Performance analysis")
    performance_subparsers = performance_parser.add_subparsers(dest="performance_command", help="Performance commands")

    for cmd, desc in [
        ("scan", "Run all performance checks"),
        ("memory", "Analyze memory usage patterns"),
        ("cpu", "Analyze CPU/complexity patterns"),
        ("database", "Analyze database access patterns"),
        ("cache", "Analyze caching patterns"),
    ]:
        sub = performance_subparsers.add_parser(cmd, help=desc)
        add_performance_args(sub)


def _setup_oop_commands(subparsers) -> None:
    """Set up OOP command group."""
    oop_parser = subparsers.add_parser("oop", help="Object-oriented metrics analysis")
    oop_subparsers = oop_parser.add_subparsers(dest="oop_command", help="OOP commands")

    for cmd, desc in [
        ("analyze", "Run all OOP metrics analysis"),
        ("coupling", "Analyze class coupling (CBO)"),
        ("cohesion", "Analyze class cohesion (LCOM)"),
        ("inheritance", "Analyze inheritance (DIT/NOC)"),
    ]:
        sub = oop_subparsers.add_parser(cmd, help=desc)
        add_oop_args(sub)


def _setup_deps_commands(subparsers) -> None:
    """Set up dependencies command group."""
    deps_parser = subparsers.add_parser("dependencies", help="Dependency analysis")
    deps_subparsers = deps_parser.add_subparsers(dest="deps_command", help="Dependency commands")

    for cmd, desc in [
        ("analyze", "Run full dependency analysis"),
        ("cycles", "Detect circular dependencies"),
        ("graph", "Build dependency graph"),
        ("modularity", "Analyze modularity"),
    ]:
        sub = deps_subparsers.add_parser(cmd, help=desc)
        add_deps_args(sub)


def _setup_arch_commands(subparsers) -> None:
    """Set up architecture command group."""
    arch_parser = subparsers.add_parser("architecture", help="Architecture analysis")
    arch_subparsers = arch_parser.add_subparsers(dest="arch_command", help="Architecture commands")

    for cmd, desc in [
        ("analyze", "Run full architecture analysis"),
        ("solid", "Validate SOLID principles"),
        ("layers", "Check layer compliance"),
        ("patterns", "Detect design patterns"),
    ]:
        sub = arch_subparsers.add_parser(cmd, help=desc)
        add_arch_args(sub)


def _setup_coverage_commands(subparsers) -> None:
    """Set up coverage command group."""
    cov_parser = subparsers.add_parser("coverage", help="Test coverage analysis")
    cov_subparsers = cov_parser.add_subparsers(dest="cov_command", help="Coverage commands")

    for cmd, desc in [
        ("analyze", "Run full coverage analysis"),
        ("gaps", "Find coverage gaps"),
        ("suggestions", "Generate test suggestions"),
    ]:
        sub = cov_subparsers.add_parser(cmd, help=desc)
        add_coverage_args(sub)


def _setup_syntax_commands(subparsers) -> None:
    """Set up syntax command group."""
    syntax_parser = subparsers.add_parser("syntax", help="Syntax and linting analysis")
    syntax_subparsers = syntax_parser.add_subparsers(dest="syntax_command", help="Syntax commands")

    for cmd, desc in [
        ("check", "Run syntax and linting checks"),
        ("fix", "Auto-fix syntax issues"),
    ]:
        sub = syntax_subparsers.add_parser(cmd, help=desc)
        add_syntax_args(sub)


def _setup_requirements_commands(subparsers) -> None:
    """Set up requirements command group."""
    req_parser = subparsers.add_parser("requirements", help="Requirements.txt validation")
    req_subparsers = req_parser.add_subparsers(dest="req_command", help="Requirements commands")

    for cmd, desc in [
        ("check", "Check requirements vs imports"),
        ("sync", "Sync requirements with imports"),
    ]:
        sub = req_subparsers.add_parser(cmd, help=desc)
        add_requirements_args(sub)


def _setup_licenses_commands(subparsers) -> None:
    """Set up licenses command group."""
    lic_parser = subparsers.add_parser("licenses", help="License compliance checking")
    lic_subparsers = lic_parser.add_subparsers(dest="lic_command", help="License commands")

    lic_check = lic_subparsers.add_parser("check", help="Check license compliance for dependencies")
    add_licenses_args(lic_check)


def _setup_logic_commands(subparsers) -> None:
    """Set up logic command group."""
    logic_parser = subparsers.add_parser("logic", help="Logic and pattern analysis")
    logic_subparsers = logic_parser.add_subparsers(dest="logic_command", help="Logic commands")

    for cmd, desc in [
        ("duplication", "Detect duplicated code"),
        ("patterns", "Detect inefficient patterns and code smells"),
        ("complexity", "Calculate code complexity"),
        ("audit", "Run all logic checks"),
    ]:
        sub = logic_subparsers.add_parser(cmd, help=desc)
        add_logic_args(sub)


def main(args=None):
    """Main entry point for the Heimdall CLI.

    Args:
        args: Optional list of arguments. If None, uses sys.argv.
    """
    parser = create_parser()
    args = parser.parse_args(args)
    verbose = args.verbose if hasattr(args, "verbose") else False

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Handle quality subcommands
    if args.command == "quality":
        if not hasattr(args, 'quality_command') or args.quality_command is None:
            print("Error: Please specify a quality command. Available commands:")
            print("  analyze, file-length, complexity, duplication, smells, debt,")
            print("  maintainability, env-fallback, lazy-imports, forbidden-imports,")
            print("  datetime, typing")
            print("\nUse 'heimdall quality <command> -h' for help on a specific command.")
            sys.exit(1)

        handlers = {
            "analyze": lambda: run_quality_analysis(args, verbose),
            "file-length": lambda: run_quality_analysis(args, verbose),
            "complexity": lambda: run_complexity_analysis(args, verbose),
            "duplication": lambda: run_duplication_analysis(args, verbose),
            "smells": lambda: run_smell_analysis(args, verbose),
            "debt": lambda: run_debt_analysis(args, verbose),
            "maintainability": lambda: run_maintainability_analysis(args, verbose),
            "env-fallback": lambda: run_env_fallback_analysis(args, verbose),
            "lazy-imports": lambda: run_lazy_imports_analysis(args, verbose),
            "forbidden-imports": lambda: run_forbidden_imports_analysis(args, verbose),
            "datetime": lambda: run_datetime_analysis(args, verbose),
            "typing": lambda: run_typing_analysis(args, verbose),
        }

        if args.quality_command in handlers:
            sys.exit(handlers[args.quality_command]())
        else:
            print(f"Unknown quality command: {args.quality_command}")
            sys.exit(1)

    # Handle audit command (alias for quality analyze)
    elif args.command == "audit":
        sys.exit(run_quality_analysis(args, verbose))

    # Handle security subcommands
    elif args.command == "security":
        if not hasattr(args, 'security_command') or args.security_command is None:
            print("Error: Please specify a security command (e.g., 'scan', 'secrets')")
            sys.exit(1)

        security_types = {
            "scan": "all", "secrets": "secrets", "dependencies": "dependencies",
            "vulnerabilities": "vulnerabilities", "crypto": "crypto", "access": "access",
            "auth": "auth", "headers": "headers", "tls": "tls", "container": "container",
            "infra": "infra"
        }

        if args.security_command in security_types:
            sys.exit(run_security_analysis(args, verbose, security_types[args.security_command]))
        else:
            print(f"Unknown security command: {args.security_command}")
            sys.exit(1)

    # Handle performance subcommands
    elif args.command == "performance":
        if not hasattr(args, 'performance_command') or args.performance_command is None:
            print("Error: Please specify a performance command (e.g., 'scan', 'memory')")
            sys.exit(1)

        perf_types = {"scan": "all", "memory": "memory", "cpu": "cpu", "database": "database", "cache": "cache"}

        if args.performance_command in perf_types:
            sys.exit(run_performance_analysis(args, verbose, perf_types[args.performance_command]))
        else:
            print(f"Unknown performance command: {args.performance_command}")
            sys.exit(1)

    # Handle OOP subcommands
    elif args.command == "oop":
        if not hasattr(args, 'oop_command') or args.oop_command is None:
            print("Error: Please specify an OOP command (e.g., 'analyze', 'coupling')")
            sys.exit(1)

        if args.oop_command in ("analyze", "coupling", "cohesion", "inheritance"):
            sys.exit(run_oop_analysis(args, verbose))
        else:
            print(f"Unknown OOP command: {args.oop_command}")
            sys.exit(1)

    # Handle dependencies subcommands
    elif args.command == "dependencies":
        if not hasattr(args, 'deps_command') or args.deps_command is None:
            print("Error: Please specify a dependencies command (e.g., 'analyze', 'cycles')")
            sys.exit(1)

        deps_types = {"analyze": "all", "cycles": "cycles", "graph": "all", "modularity": "modularity"}

        if args.deps_command in deps_types:
            sys.exit(run_deps_analysis(args, verbose, deps_types[args.deps_command]))
        else:
            print(f"Unknown dependencies command: {args.deps_command}")
            sys.exit(1)

    # Handle architecture subcommands
    elif args.command == "architecture":
        if not hasattr(args, 'arch_command') or args.arch_command is None:
            print("Error: Please specify an architecture command (e.g., 'analyze', 'solid')")
            sys.exit(1)

        arch_types = {"analyze": "all", "solid": "solid", "layers": "layers", "patterns": "patterns"}

        if args.arch_command in arch_types:
            sys.exit(run_arch_analysis(args, verbose, arch_types[args.arch_command]))
        else:
            print(f"Unknown architecture command: {args.arch_command}")
            sys.exit(1)

    # Handle coverage subcommands
    elif args.command == "coverage":
        if not hasattr(args, 'cov_command') or args.cov_command is None:
            print("Error: Please specify a coverage command (e.g., 'analyze', 'gaps')")
            sys.exit(1)

        cov_types = {"analyze": "all", "gaps": "gaps", "suggestions": "suggestions"}

        if args.cov_command in cov_types:
            sys.exit(run_coverage_analysis(args, verbose, cov_types[args.cov_command]))
        else:
            print(f"Unknown coverage command: {args.cov_command}")
            sys.exit(1)

    # Handle syntax subcommands
    elif args.command == "syntax":
        if not hasattr(args, 'syntax_command') or args.syntax_command is None:
            print("Error: Please specify a syntax command (e.g., 'check', 'fix')")
            sys.exit(1)

        if args.syntax_command == "check":
            sys.exit(run_syntax_analysis(args, verbose, fix_mode=False))
        elif args.syntax_command == "fix":
            sys.exit(run_syntax_analysis(args, verbose, fix_mode=True))
        else:
            print(f"Unknown syntax command: {args.syntax_command}")
            sys.exit(1)

    # Handle requirements subcommands
    elif args.command == "requirements":
        if not hasattr(args, 'req_command') or args.req_command is None:
            print("Error: Please specify a requirements command (e.g., 'check', 'sync')")
            sys.exit(1)

        if args.req_command == "check":
            sys.exit(run_requirements_analysis(args, verbose, sync_mode=False))
        elif args.req_command == "sync":
            sys.exit(run_requirements_analysis(args, verbose, sync_mode=True))
        else:
            print(f"Unknown requirements command: {args.req_command}")
            sys.exit(1)

    # Handle licenses subcommands
    elif args.command == "licenses":
        if not hasattr(args, 'lic_command') or args.lic_command is None:
            print("Error: Please specify a licenses command (e.g., 'check')")
            sys.exit(1)

        if args.lic_command == "check":
            sys.exit(run_licenses_analysis(args, verbose))
        else:
            print(f"Unknown licenses command: {args.lic_command}")
            sys.exit(1)

    # Handle logic subcommands
    elif args.command == "logic":
        if not hasattr(args, 'logic_command') or args.logic_command is None:
            print("Error: Please specify a logic command (e.g., 'duplication', 'patterns', 'complexity', 'audit')")
            sys.exit(1)

        logic_types = {"duplication": "duplication", "patterns": "patterns", "complexity": "complexity", "audit": "audit"}

        if args.logic_command in logic_types:
            sys.exit(run_logic_analysis(args, verbose, analysis_type=logic_types[args.logic_command]))
        else:
            print(f"Unknown logic command: {args.logic_command}")
            sys.exit(1)

    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
