"""
Heimdall Shell Script Analyzer

Performs regex-based static analysis on shell and bash script files.
Files are discovered by extension (.sh, .bash) and optionally by shebang
line (#!/bin/bash, #!/bin/sh, #!/usr/bin/env bash).
"""

import fnmatch
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from Asgard.Heimdall.Quality.languages.shell.models.shell_models import (
    ShellAnalysisConfig,
    ShellFinding,
    ShellReport,
    ShellRuleCategory,
    ShellSeverity,
)

_SHELL_SHEBANGS = (
    "#!/bin/bash",
    "#!/bin/sh",
    "#!/usr/bin/env bash",
)


def _make_finding(
    file_path: str,
    line_number: int,
    rule_id: str,
    category: ShellRuleCategory,
    severity: ShellSeverity,
    title: str,
    description: str,
    code_snippet: str = "",
    fix_suggestion: str = "",
) -> ShellFinding:
    """Construct a ShellFinding with consistent defaults."""
    return ShellFinding(
        file_path=file_path,
        line_number=line_number,
        rule_id=rule_id,
        category=category,
        severity=severity,
        title=title,
        description=description,
        code_snippet=code_snippet.rstrip(),
        fix_suggestion=fix_suggestion,
    )


class ShellAnalyzer:
    """
    Regex-based static analyzer for shell script files.

    Each public rule method returns a list of ShellFinding objects for a
    single file.  The top-level analyze() method discovers files, runs all
    enabled rules, and returns an aggregated ShellReport.
    """

    def __init__(self, config: Optional[ShellAnalysisConfig] = None) -> None:
        self._config = config or ShellAnalysisConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, scan_path: Optional[str] = None) -> ShellReport:
        """
        Analyze all matching shell script files under scan_path.

        Args:
            scan_path: Optional override for the config scan path.

        Returns:
            ShellReport containing all findings.
        """
        start = datetime.now()
        root = Path(scan_path).resolve() if scan_path else self._config.scan_path.resolve()
        report = ShellReport(scan_path=str(root))

        files = self._discover_files(root)
        report.files_analyzed = len(files)

        for file_path in files:
            try:
                source_lines = Path(file_path).read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue

            for finding in self._analyze_file(str(file_path), source_lines):
                report.add_finding(finding)

        report.scan_duration_seconds = (datetime.now() - start).total_seconds()
        return report

    # ------------------------------------------------------------------
    # File discovery
    # ------------------------------------------------------------------

    def _discover_files(self, root: Path) -> List[Path]:
        """Return all shell script files matching extensions or shebang."""
        results: set = set()

        for ext in self._config.include_extensions:
            for candidate in root.rglob(f"*{ext}"):
                if not self._is_excluded(candidate):
                    results.add(candidate)

        if self._config.also_check_shebangs:
            for candidate in root.rglob("*"):
                if candidate.is_file() and not self._is_excluded(candidate):
                    if candidate.suffix not in self._config.include_extensions:
                        if self._has_shell_shebang(candidate):
                            results.add(candidate)

        return sorted(results)

    def _has_shell_shebang(self, path: Path) -> bool:
        """Return True if the first line of the file is a recognized shell shebang."""
        try:
            first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
            return any(first_line.startswith(shebang) for shebang in _SHELL_SHEBANGS)
        except (OSError, IndexError):
            return False

    def _is_excluded(self, path: Path) -> bool:
        """Return True if the path matches any exclusion pattern."""
        parts = path.parts
        for pattern in self._config.exclude_patterns:
            for part in parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
        return False

    def _is_rule_enabled(self, rule_id: str) -> bool:
        """Return True when the rule should be executed."""
        if rule_id in self._config.disabled_rules:
            return False
        if self._config.enabled_rules is not None:
            return rule_id in self._config.enabled_rules
        return True

    # ------------------------------------------------------------------
    # Per-file analysis dispatch
    # ------------------------------------------------------------------

    def _analyze_file(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """Run all enabled rules against a single file's source lines."""
        findings: List[ShellFinding] = []
        findings.extend(self._check_eval_injection(file_path, lines))
        findings.extend(self._check_curl_insecure(file_path, lines))
        findings.extend(self._check_wget_no_check(file_path, lines))
        findings.extend(self._check_hardcoded_secret(file_path, lines))
        findings.extend(self._check_sudo_usage(file_path, lines))
        findings.extend(self._check_missing_set_e(file_path, lines))
        findings.extend(self._check_missing_set_u(file_path, lines))
        findings.extend(self._check_cd_without_check(file_path, lines))
        findings.extend(self._check_unquoted_dollar_star(file_path, lines))
        findings.extend(self._check_trailing_whitespace(file_path, lines))
        findings.extend(self._check_max_line_length(file_path, lines))
        findings.extend(self._check_function_keyword(file_path, lines))
        return findings

    # ------------------------------------------------------------------
    # Security rules
    # ------------------------------------------------------------------

    def _check_eval_injection(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """shell.eval-injection: eval with a variable argument."""
        if not self._is_rule_enabled("shell.eval-injection"):
            return []
        findings: List[ShellFinding] = []
        pattern = re.compile(r"\beval\s+\$")
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="shell.eval-injection",
                    category=ShellRuleCategory.SECURITY,
                    severity=ShellSeverity.ERROR,
                    title="eval with variable argument (code injection risk)",
                    description="Using eval with a variable can execute arbitrary code if the variable is user-controlled.",
                    code_snippet=line,
                    fix_suggestion="Avoid eval. Refactor to use explicit commands or arrays.",
                ))
        return findings

    def _check_curl_insecure(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """shell.curl-insecure: curl with -k or --insecure flag."""
        if not self._is_rule_enabled("shell.curl-insecure"):
            return []
        findings: List[ShellFinding] = []
        pattern = re.compile(r"curl\s+.*(-k\b|--insecure)")
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="shell.curl-insecure",
                    category=ShellRuleCategory.SECURITY,
                    severity=ShellSeverity.WARNING,
                    title="curl called with TLS verification disabled",
                    description="Using -k or --insecure disables TLS certificate verification and is a security risk.",
                    code_snippet=line,
                    fix_suggestion="Remove the -k/--insecure flag and use a proper certificate bundle.",
                ))
        return findings

    def _check_wget_no_check(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """shell.wget-no-check: wget with --no-check-certificate."""
        if not self._is_rule_enabled("shell.wget-no-check"):
            return []
        findings: List[ShellFinding] = []
        pattern = re.compile(r"wget\s+.*--no-check-certificate")
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="shell.wget-no-check",
                    category=ShellRuleCategory.SECURITY,
                    severity=ShellSeverity.WARNING,
                    title="wget called with certificate verification disabled",
                    description="--no-check-certificate disables TLS certificate verification.",
                    code_snippet=line,
                    fix_suggestion="Remove --no-check-certificate and use a proper certificate bundle.",
                ))
        return findings

    def _check_hardcoded_secret(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """shell.hardcoded-secret: credential variable assigned a literal string."""
        if not self._is_rule_enabled("shell.hardcoded-secret"):
            return []
        findings: List[ShellFinding] = []
        pattern = re.compile(
            r"(PASSWORD|PASSWD|SECRET|API_KEY|TOKEN)\s*=\s*['\"][^'\"]+['\"]\s*$",
            re.IGNORECASE,
        )
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="shell.hardcoded-secret",
                    category=ShellRuleCategory.SECURITY,
                    severity=ShellSeverity.WARNING,
                    title="Hardcoded credential or secret value",
                    description=(
                        "A variable with a sensitive name is assigned a string literal. "
                        "Hardcoded secrets should never be stored in source code."
                    ),
                    code_snippet=line,
                    fix_suggestion="Read secrets from environment variables or a secrets manager.",
                ))
        return findings

    def _check_sudo_usage(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """shell.sudo-usage: use of sudo."""
        if not self._is_rule_enabled("shell.sudo-usage"):
            return []
        findings: List[ShellFinding] = []
        pattern = re.compile(r"\bsudo\s+")
        for idx, line in enumerate(lines, start=1):
            # Skip comment lines
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="shell.sudo-usage",
                    category=ShellRuleCategory.SECURITY,
                    severity=ShellSeverity.INFO,
                    title="Use of sudo",
                    description="sudo grants elevated privileges. Ensure this is intentional and necessary.",
                    code_snippet=line,
                    fix_suggestion="Document why elevated privileges are required or find an alternative.",
                ))
        return findings

    # ------------------------------------------------------------------
    # Bug rules
    # ------------------------------------------------------------------

    def _check_missing_set_e(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """shell.missing-set-e: file has no 'set -e' or 'set -o errexit'."""
        if not self._is_rule_enabled("shell.missing-set-e"):
            return []
        source = "\n".join(lines)
        has_set_e = bool(re.search(r"set\s+-[a-z]*e[a-z]*", source)) or bool(
            re.search(r"set\s+-o\s+errexit", source)
        )
        if not has_set_e:
            return [_make_finding(
                file_path=file_path,
                line_number=1,
                rule_id="shell.missing-set-e",
                category=ShellRuleCategory.BUG,
                severity=ShellSeverity.INFO,
                title="Missing 'set -e' (errexit)",
                description=(
                    "Without 'set -e', the script will continue executing after a command fails, "
                    "potentially producing incorrect results silently."
                ),
                fix_suggestion="Add 'set -e' or 'set -o errexit' near the top of the script.",
            )]
        return []

    def _check_missing_set_u(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """shell.missing-set-u: file has no 'set -u' or 'set -o nounset'."""
        if not self._is_rule_enabled("shell.missing-set-u"):
            return []
        source = "\n".join(lines)
        has_set_u = bool(re.search(r"set\s+-[a-z]*u[a-z]*", source)) or bool(
            re.search(r"set\s+-o\s+nounset", source)
        )
        if not has_set_u:
            return [_make_finding(
                file_path=file_path,
                line_number=1,
                rule_id="shell.missing-set-u",
                category=ShellRuleCategory.BUG,
                severity=ShellSeverity.INFO,
                title="Missing 'set -u' (nounset)",
                description=(
                    "Without 'set -u', unset variables expand to an empty string silently, "
                    "which can lead to data loss (e.g., 'rm -rf /$UNSET_VAR')."
                ),
                fix_suggestion="Add 'set -u' or 'set -o nounset' near the top of the script.",
            )]
        return []

    def _check_cd_without_check(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """shell.cd-without-check: cd not followed by || or &&."""
        if not self._is_rule_enabled("shell.cd-without-check"):
            return []
        findings: List[ShellFinding] = []
        # Match cd commands not followed by || or &&
        # Line ends without a pipe/ampersand continuation
        pattern = re.compile(r"\bcd\s+[^|&;]*$")
        for idx, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="shell.cd-without-check",
                    category=ShellRuleCategory.BUG,
                    severity=ShellSeverity.WARNING,
                    title="cd without error check",
                    description=(
                        "If cd fails (e.g., directory does not exist), subsequent commands will run "
                        "in the wrong directory. Always check the return value of cd."
                    ),
                    code_snippet=line,
                    fix_suggestion="Use 'cd /some/path || exit 1' or 'cd /some/path || { echo \"fail\"; exit 1; }'.",
                ))
        return findings

    def _check_unquoted_dollar_star(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """shell.unquoted-dollar-star: $* not inside double quotes."""
        if not self._is_rule_enabled("shell.unquoted-dollar-star"):
            return []
        findings: List[ShellFinding] = []
        # Simple heuristic: flag $* that is not directly preceded by a double quote
        pattern = re.compile(r'(?<!")\$\*(?!")')
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="shell.unquoted-dollar-star",
                    category=ShellRuleCategory.BUG,
                    severity=ShellSeverity.WARNING,
                    title="Unquoted $*",
                    description=(
                        "Unquoted $* causes word splitting and glob expansion. "
                        "Use \"$@\" to preserve argument boundaries."
                    ),
                    code_snippet=line,
                    fix_suggestion='Replace $* with "$@" to correctly handle arguments with spaces.',
                ))
        return findings

    # ------------------------------------------------------------------
    # Style / Portability rules
    # ------------------------------------------------------------------

    def _check_trailing_whitespace(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """shell.trailing-whitespace: lines with trailing whitespace."""
        if not self._is_rule_enabled("shell.trailing-whitespace"):
            return []
        findings: List[ShellFinding] = []
        pattern = re.compile(r"\s+$")
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="shell.trailing-whitespace",
                    category=ShellRuleCategory.STYLE,
                    severity=ShellSeverity.INFO,
                    title="Trailing whitespace",
                    description="This line has trailing whitespace characters.",
                    code_snippet=line,
                    fix_suggestion="Remove trailing whitespace.",
                ))
        return findings

    def _check_max_line_length(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """shell.max-line-length: lines exceeding 120 characters."""
        if not self._is_rule_enabled("shell.max-line-length"):
            return []
        findings: List[ShellFinding] = []
        for idx, line in enumerate(lines, start=1):
            if len(line) > 120:
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="shell.max-line-length",
                    category=ShellRuleCategory.STYLE,
                    severity=ShellSeverity.INFO,
                    title=f"Line exceeds 120 characters ({len(line)} chars)",
                    description=f"This line is {len(line)} characters long, exceeding the 120-character limit.",
                    code_snippet=line[:120] + "...",
                    fix_suggestion="Break the line with a backslash continuation or refactor the command.",
                ))
        return findings

    def _check_function_keyword(self, file_path: str, lines: List[str]) -> List[ShellFinding]:
        """shell.function-keyword: non-POSIX 'function' keyword used."""
        if not self._is_rule_enabled("shell.function-keyword"):
            return []
        findings: List[ShellFinding] = []
        pattern = re.compile(r"\bfunction\s+\w+\s*\(\)")
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="shell.function-keyword",
                    category=ShellRuleCategory.PORTABILITY,
                    severity=ShellSeverity.INFO,
                    title="Non-POSIX 'function' keyword",
                    description=(
                        "The 'function' keyword is a bash extension and not POSIX-compliant. "
                        "Scripts intended to be portable should use the 'name() {}' syntax instead."
                    ),
                    code_snippet=line,
                    fix_suggestion="Replace 'function foo()' with 'foo()'.",
                ))
        return findings
