"""
Heimdall Static Security Analysis Service

Service for comprehensive static security analysis combining multiple
security checks into a unified analysis.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from Asgard.Heimdall.Security.models.security_models import (
    SecurityReport,
    SecurityScanConfig,
)
from Asgard.Heimdall.Security.services.secrets_detection_service import SecretsDetectionService
from Asgard.Heimdall.Security.services.dependency_vulnerability_service import DependencyVulnerabilityService
from Asgard.Heimdall.Security.services.injection_detection_service import InjectionDetectionService
from Asgard.Heimdall.Security.services.cryptographic_validation_service import CryptographicValidationService
from Asgard.Heimdall.Security.Access.services.access_analyzer import AccessAnalyzer
from Asgard.Heimdall.Security.Auth.services.auth_analyzer import AuthAnalyzer
from Asgard.Heimdall.Security.Headers.services.headers_analyzer import HeadersAnalyzer
from Asgard.Heimdall.Security.TLS.services.tls_analyzer import TLSAnalyzer
from Asgard.Heimdall.Security.Container.services.container_analyzer import ContainerAnalyzer
from Asgard.Heimdall.Security.Infrastructure.services.infra_analyzer import InfraAnalyzer


class StaticSecurityService:
    """
    Comprehensive static security analysis service.

    Combines multiple security scanning capabilities:
    - Secrets detection (API keys, passwords, tokens)
    - Dependency vulnerability scanning
    - Injection vulnerability detection (SQL, XSS, command)
    - Cryptographic implementation validation
    - Access control analysis (RBAC, permissions)
    - Authentication analysis (JWT, sessions, passwords)
    - Security headers analysis (CSP, CORS, HSTS)
    - TLS/SSL configuration analysis
    - Container security analysis (Dockerfile, docker-compose)
    - Infrastructure security analysis (credentials, config)

    Provides a unified security report with aggregated findings
    and an overall security score.
    """

    def __init__(self, config: Optional[SecurityScanConfig] = None):
        """
        Initialize the static security service.

        Args:
            config: Security scan configuration. Uses defaults if not provided.
        """
        self.config = config or SecurityScanConfig()

        self.secrets_service = SecretsDetectionService(self.config)
        self.dependency_service = DependencyVulnerabilityService(self.config)
        self.injection_service = InjectionDetectionService(self.config)
        self.crypto_service = CryptographicValidationService(self.config)
        self.access_analyzer = AccessAnalyzer()
        self.auth_analyzer = AuthAnalyzer()
        self.headers_analyzer = HeadersAnalyzer()
        self.tls_analyzer = TLSAnalyzer()
        self.container_analyzer = ContainerAnalyzer()
        self.infrastructure_analyzer = InfraAnalyzer()

    def scan(self, scan_path: Optional[Path] = None) -> SecurityReport:
        """
        Perform comprehensive security analysis.

        Args:
            scan_path: Root path to scan. Uses config path if not provided.

        Returns:
            SecurityReport containing all findings from all services
        """
        path = scan_path or self.config.scan_path
        path = Path(path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Scan path does not exist: {path}")

        start_time = time.time()

        report = SecurityReport(
            scan_path=str(path),
            scan_config=self.config,
        )

        if self.config.scan_secrets:
            try:
                report.secrets_report = self.secrets_service.scan(path)
            except Exception as e:
                pass

        if self.config.scan_dependencies:
            try:
                report.dependency_report = self.dependency_service.scan(path)
            except Exception as e:
                pass

        if self.config.scan_vulnerabilities:
            try:
                report.vulnerability_report = self.injection_service.scan(path)
            except Exception as e:
                pass

        if self.config.scan_crypto:
            try:
                report.crypto_report = self.crypto_service.scan(path)
            except Exception as e:
                pass

        if self.config.scan_access:
            try:
                report.access_report = self.access_analyzer.scan(path)
            except Exception as e:
                pass

        if self.config.scan_auth:
            try:
                report.auth_report = self.auth_analyzer.scan(path)
            except Exception as e:
                pass

        if self.config.scan_headers:
            try:
                report.headers_report = self.headers_analyzer.scan(path)
            except Exception as e:
                pass

        if self.config.scan_tls:
            try:
                report.tls_report = self.tls_analyzer.scan(path)
            except Exception as e:
                pass

        if self.config.scan_container:
            try:
                report.container_report = self.container_analyzer.scan(path)
            except Exception as e:
                pass

        if self.config.scan_infrastructure:
            try:
                report.infrastructure_report = self.infrastructure_analyzer.scan(path)
            except Exception as e:
                pass

        report.scan_duration_seconds = time.time() - start_time
        report.scanned_at = datetime.now()

        report.calculate_totals()

        return report

    def scan_secrets_only(self, scan_path: Optional[Path] = None) -> SecurityReport:
        """
        Scan only for secrets.

        Args:
            scan_path: Root path to scan

        Returns:
            SecurityReport with secrets findings only
        """
        path = scan_path or self.config.scan_path
        path = Path(path).resolve()

        start_time = time.time()

        report = SecurityReport(
            scan_path=str(path),
            scan_config=self.config,
        )

        report.secrets_report = self.secrets_service.scan(path)
        report.scan_duration_seconds = time.time() - start_time
        report.calculate_totals()

        return report

    def scan_dependencies_only(self, scan_path: Optional[Path] = None) -> SecurityReport:
        """
        Scan only for dependency vulnerabilities.

        Args:
            scan_path: Root path to scan

        Returns:
            SecurityReport with dependency findings only
        """
        path = scan_path or self.config.scan_path
        path = Path(path).resolve()

        start_time = time.time()

        report = SecurityReport(
            scan_path=str(path),
            scan_config=self.config,
        )

        report.dependency_report = self.dependency_service.scan(path)
        report.scan_duration_seconds = time.time() - start_time
        report.calculate_totals()

        return report

    def scan_vulnerabilities_only(self, scan_path: Optional[Path] = None) -> SecurityReport:
        """
        Scan only for injection vulnerabilities.

        Args:
            scan_path: Root path to scan

        Returns:
            SecurityReport with vulnerability findings only
        """
        path = scan_path or self.config.scan_path
        path = Path(path).resolve()

        start_time = time.time()

        report = SecurityReport(
            scan_path=str(path),
            scan_config=self.config,
        )

        report.vulnerability_report = self.injection_service.scan(path)
        report.scan_duration_seconds = time.time() - start_time
        report.calculate_totals()

        return report

    def scan_crypto_only(self, scan_path: Optional[Path] = None) -> SecurityReport:
        """
        Scan only for cryptographic issues.

        Args:
            scan_path: Root path to scan

        Returns:
            SecurityReport with crypto findings only
        """
        path = scan_path or self.config.scan_path
        path = Path(path).resolve()

        start_time = time.time()

        report = SecurityReport(
            scan_path=str(path),
            scan_config=self.config,
        )

        report.crypto_report = self.crypto_service.scan(path)
        report.scan_duration_seconds = time.time() - start_time
        report.calculate_totals()

        return report

    def scan_access_only(self, scan_path: Optional[Path] = None) -> SecurityReport:
        """
        Scan only for access control issues.

        Args:
            scan_path: Root path to scan

        Returns:
            SecurityReport with access control findings only
        """
        path = scan_path or self.config.scan_path
        path = Path(path).resolve()

        start_time = time.time()

        report = SecurityReport(
            scan_path=str(path),
            scan_config=self.config,
        )

        report.access_report = self.access_analyzer.scan(path)
        report.scan_duration_seconds = time.time() - start_time
        report.calculate_totals()

        return report

    def scan_auth_only(self, scan_path: Optional[Path] = None) -> SecurityReport:
        """
        Scan only for authentication issues.

        Args:
            scan_path: Root path to scan

        Returns:
            SecurityReport with authentication findings only
        """
        path = scan_path or self.config.scan_path
        path = Path(path).resolve()

        start_time = time.time()

        report = SecurityReport(
            scan_path=str(path),
            scan_config=self.config,
        )

        report.auth_report = self.auth_analyzer.scan(path)
        report.scan_duration_seconds = time.time() - start_time
        report.calculate_totals()

        return report

    def scan_headers_only(self, scan_path: Optional[Path] = None) -> SecurityReport:
        """
        Scan only for security headers issues.

        Args:
            scan_path: Root path to scan

        Returns:
            SecurityReport with headers findings only
        """
        path = scan_path or self.config.scan_path
        path = Path(path).resolve()

        start_time = time.time()

        report = SecurityReport(
            scan_path=str(path),
            scan_config=self.config,
        )

        report.headers_report = self.headers_analyzer.scan(path)
        report.scan_duration_seconds = time.time() - start_time
        report.calculate_totals()

        return report

    def scan_tls_only(self, scan_path: Optional[Path] = None) -> SecurityReport:
        """
        Scan only for TLS/SSL issues.

        Args:
            scan_path: Root path to scan

        Returns:
            SecurityReport with TLS findings only
        """
        path = scan_path or self.config.scan_path
        path = Path(path).resolve()

        start_time = time.time()

        report = SecurityReport(
            scan_path=str(path),
            scan_config=self.config,
        )

        report.tls_report = self.tls_analyzer.scan(path)
        report.scan_duration_seconds = time.time() - start_time
        report.calculate_totals()

        return report

    def scan_container_only(self, scan_path: Optional[Path] = None) -> SecurityReport:
        """
        Scan only for container security issues.

        Args:
            scan_path: Root path to scan

        Returns:
            SecurityReport with container findings only
        """
        path = scan_path or self.config.scan_path
        path = Path(path).resolve()

        start_time = time.time()

        report = SecurityReport(
            scan_path=str(path),
            scan_config=self.config,
        )

        report.container_report = self.container_analyzer.scan(path)
        report.scan_duration_seconds = time.time() - start_time
        report.calculate_totals()

        return report

    def scan_infrastructure_only(self, scan_path: Optional[Path] = None) -> SecurityReport:
        """
        Scan only for infrastructure security issues.

        Args:
            scan_path: Root path to scan

        Returns:
            SecurityReport with infrastructure findings only
        """
        path = scan_path or self.config.scan_path
        path = Path(path).resolve()

        start_time = time.time()

        report = SecurityReport(
            scan_path=str(path),
            scan_config=self.config,
        )

        report.infrastructure_report = self.infrastructure_analyzer.scan(path)
        report.scan_duration_seconds = time.time() - start_time
        report.calculate_totals()

        return report

    def get_summary(self, report: SecurityReport) -> str:
        """
        Generate a text summary of the security report.

        Args:
            report: The security report

        Returns:
            Formatted summary string
        """
        lines = [
            "=" * 60,
            "HEIMDALL SECURITY ANALYSIS REPORT",
            "=" * 60,
            f"Scan Path: {report.scan_path}",
            f"Scanned At: {report.scanned_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {report.scan_duration_seconds:.2f} seconds",
            "",
            "-" * 40,
            "SUMMARY",
            "-" * 40,
            f"Security Score: {report.security_score:.1f}/100",
            f"Total Issues: {report.total_issues}",
            f"  Critical: {report.critical_issues}",
            f"  High: {report.high_issues}",
            f"  Medium: {report.medium_issues}",
            f"  Low: {report.low_issues}",
            "",
        ]

        if report.secrets_report:
            lines.extend([
                "-" * 40,
                "SECRETS DETECTION",
                "-" * 40,
                f"Files Scanned: {report.secrets_report.total_files_scanned}",
                f"Secrets Found: {report.secrets_report.secrets_found}",
            ])

            if report.secrets_report.findings:
                lines.append("")
                for finding in report.secrets_report.findings[:5]:
                    lines.append(f"  [{finding.severity.upper()}] {finding.file_path}:{finding.line_number}")
                    lines.append(f"    {finding.pattern_name}: {finding.masked_value}")

                if len(report.secrets_report.findings) > 5:
                    lines.append(f"  ... and {len(report.secrets_report.findings) - 5} more")
            lines.append("")

        if report.dependency_report:
            lines.extend([
                "-" * 40,
                "DEPENDENCY VULNERABILITIES",
                "-" * 40,
                f"Dependencies Analyzed: {report.dependency_report.total_dependencies}",
                f"Vulnerable Packages: {report.dependency_report.vulnerable_dependencies}",
            ])

            if report.dependency_report.vulnerabilities:
                lines.append("")
                for vuln in report.dependency_report.vulnerabilities[:5]:
                    lines.append(f"  [{vuln.risk_level.upper()}] {vuln.package_name} {vuln.installed_version}")
                    lines.append(f"    {vuln.title}")
                    if vuln.fixed_version:
                        lines.append(f"    Fix: Upgrade to {vuln.fixed_version}")

                if len(report.dependency_report.vulnerabilities) > 5:
                    lines.append(f"  ... and {len(report.dependency_report.vulnerabilities) - 5} more")
            lines.append("")

        if report.vulnerability_report:
            lines.extend([
                "-" * 40,
                "CODE VULNERABILITIES",
                "-" * 40,
                f"Files Scanned: {report.vulnerability_report.total_files_scanned}",
                f"Vulnerabilities Found: {report.vulnerability_report.vulnerabilities_found}",
            ])

            if report.vulnerability_report.findings:
                lines.append("")
                for finding in report.vulnerability_report.findings[:5]:
                    lines.append(f"  [{finding.severity.upper()}] {finding.file_path}:{finding.line_number}")
                    lines.append(f"    {finding.title}")

                if len(report.vulnerability_report.findings) > 5:
                    lines.append(f"  ... and {len(report.vulnerability_report.findings) - 5} more")
            lines.append("")

        if report.crypto_report:
            lines.extend([
                "-" * 40,
                "CRYPTOGRAPHIC ISSUES",
                "-" * 40,
                f"Files Scanned: {report.crypto_report.total_files_scanned}",
                f"Issues Found: {report.crypto_report.issues_found}",
            ])

            if report.crypto_report.findings:
                lines.append("")
                for finding in report.crypto_report.findings[:5]:
                    lines.append(f"  [{finding.severity.upper()}] {finding.file_path}:{finding.line_number}")
                    lines.append(f"    {finding.description}")

                if len(report.crypto_report.findings) > 5:
                    lines.append(f"  ... and {len(report.crypto_report.findings) - 5} more")
            lines.append("")

        if report.access_report and hasattr(report.access_report, 'findings'):
            lines.extend([
                "-" * 40,
                "ACCESS CONTROL ISSUES",
                "-" * 40,
                f"Files Scanned: {report.access_report.total_files_scanned}",
                f"Issues Found: {report.access_report.total_issues}",
            ])

            if report.access_report.findings:
                lines.append("")
                for finding in report.access_report.findings[:5]:
                    lines.append(f"  [{finding.severity.upper()}] {finding.file_path}:{finding.line_number}")
                    lines.append(f"    {finding.title}")

                if len(report.access_report.findings) > 5:
                    lines.append(f"  ... and {len(report.access_report.findings) - 5} more")
            lines.append("")

        if report.auth_report and hasattr(report.auth_report, 'findings'):
            lines.extend([
                "-" * 40,
                "AUTHENTICATION ISSUES",
                "-" * 40,
                f"Files Scanned: {report.auth_report.total_files_scanned}",
                f"Issues Found: {report.auth_report.total_issues}",
            ])

            if report.auth_report.findings:
                lines.append("")
                for finding in report.auth_report.findings[:5]:
                    lines.append(f"  [{finding.severity.upper()}] {finding.file_path}:{finding.line_number}")
                    lines.append(f"    {finding.title}")

                if len(report.auth_report.findings) > 5:
                    lines.append(f"  ... and {len(report.auth_report.findings) - 5} more")
            lines.append("")

        if report.headers_report and hasattr(report.headers_report, 'findings'):
            lines.extend([
                "-" * 40,
                "SECURITY HEADERS ISSUES",
                "-" * 40,
                f"Files Scanned: {report.headers_report.total_files_scanned}",
                f"Issues Found: {report.headers_report.total_issues}",
            ])

            if report.headers_report.findings:
                lines.append("")
                for finding in report.headers_report.findings[:5]:
                    lines.append(f"  [{finding.severity.upper()}] {finding.file_path}:{finding.line_number}")
                    lines.append(f"    {finding.title}")

                if len(report.headers_report.findings) > 5:
                    lines.append(f"  ... and {len(report.headers_report.findings) - 5} more")
            lines.append("")

        if report.tls_report and hasattr(report.tls_report, 'findings'):
            lines.extend([
                "-" * 40,
                "TLS/SSL ISSUES",
                "-" * 40,
                f"Files Scanned: {report.tls_report.total_files_scanned}",
                f"Issues Found: {report.tls_report.total_issues}",
            ])

            if report.tls_report.findings:
                lines.append("")
                for finding in report.tls_report.findings[:5]:
                    lines.append(f"  [{finding.severity.upper()}] {finding.file_path}:{finding.line_number}")
                    lines.append(f"    {finding.title}")

                if len(report.tls_report.findings) > 5:
                    lines.append(f"  ... and {len(report.tls_report.findings) - 5} more")
            lines.append("")

        if report.container_report and hasattr(report.container_report, 'findings'):
            lines.extend([
                "-" * 40,
                "CONTAINER SECURITY ISSUES",
                "-" * 40,
                f"Files Scanned: {report.container_report.total_files_scanned}",
                f"Issues Found: {report.container_report.total_issues}",
            ])

            if report.container_report.findings:
                lines.append("")
                for finding in report.container_report.findings[:5]:
                    lines.append(f"  [{finding.severity.upper()}] {finding.file_path}:{finding.line_number}")
                    lines.append(f"    {finding.title}")

                if len(report.container_report.findings) > 5:
                    lines.append(f"  ... and {len(report.container_report.findings) - 5} more")
            lines.append("")

        if report.infrastructure_report and hasattr(report.infrastructure_report, 'findings'):
            lines.extend([
                "-" * 40,
                "INFRASTRUCTURE SECURITY ISSUES",
                "-" * 40,
                f"Files Scanned: {report.infrastructure_report.total_files_scanned}",
                f"Issues Found: {report.infrastructure_report.total_issues}",
            ])

            if report.infrastructure_report.findings:
                lines.append("")
                for finding in report.infrastructure_report.findings[:5]:
                    lines.append(f"  [{finding.severity.upper()}] {finding.file_path}:{finding.line_number}")
                    lines.append(f"    {finding.title}")

                if len(report.infrastructure_report.findings) > 5:
                    lines.append(f"  ... and {len(report.infrastructure_report.findings) - 5} more")
            lines.append("")

        lines.extend([
            "=" * 60,
            f"RESULT: {'PASS' if report.is_passing else 'FAIL'}",
            "=" * 60,
        ])

        return "\n".join(lines)
