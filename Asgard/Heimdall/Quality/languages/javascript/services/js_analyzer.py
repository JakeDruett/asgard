"""
Heimdall JavaScript Analyzer

Performs regex-based static analysis on JavaScript and JSX source files.
Because Python's ast module cannot parse JS/TS, all rules are implemented
using line-by-line regular expression matching.
"""

import fnmatch
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from Asgard.Heimdall.Quality.languages.javascript.models.js_models import (
    JSAnalysisConfig,
    JSFinding,
    JSReport,
    JSRuleCategory,
    JSSeverity,
)


def _make_finding(
    file_path: str,
    line_number: int,
    rule_id: str,
    category: JSRuleCategory,
    severity: JSSeverity,
    title: str,
    description: str,
    code_snippet: str = "",
    fix_suggestion: str = "",
    column: int = 0,
) -> JSFinding:
    """Construct a JSFinding with consistent defaults."""
    return JSFinding(
        file_path=file_path,
        line_number=line_number,
        column=column,
        rule_id=rule_id,
        category=category,
        severity=severity,
        title=title,
        description=description,
        code_snippet=code_snippet.rstrip(),
        fix_suggestion=fix_suggestion,
    )


class JSAnalyzer:
    """
    Regex-based static analyzer for JavaScript and JSX files.

    Each public rule method returns a list of JSFinding objects for a single
    file.  The top-level analyze() method discovers files, runs all enabled
    rules, and returns an aggregated JSReport.
    """

    def __init__(self, config: Optional[JSAnalysisConfig] = None) -> None:
        self._config = config or JSAnalysisConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, scan_path: Optional[str] = None) -> JSReport:
        """
        Analyze all matching source files under scan_path.

        Args:
            scan_path: Optional override for the config scan path.

        Returns:
            JSReport containing all findings.
        """
        start = datetime.now()
        root = Path(scan_path).resolve() if scan_path else self._config.scan_path.resolve()
        report = JSReport(scan_path=str(root), language=self._config.language)

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
        """Return all files matching the configured extensions, excluding patterns."""
        results: List[Path] = []
        for ext in self._config.include_extensions:
            for candidate in root.rglob(f"*{ext}"):
                if not self._is_excluded(candidate):
                    results.append(candidate)
        return sorted(set(results))

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

    def _analyze_file(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """Run all enabled rules against a single file's source lines."""
        findings: List[JSFinding] = []
        findings.extend(self._check_no_eval(file_path, lines))
        findings.extend(self._check_no_implied_eval(file_path, lines))
        findings.extend(self._check_no_debugger(file_path, lines))
        findings.extend(self._check_eqeqeq(file_path, lines))
        findings.extend(self._check_no_alert(file_path, lines))
        findings.extend(self._check_no_var(file_path, lines))
        findings.extend(self._check_no_empty_block(file_path, lines))
        findings.extend(self._check_no_console(file_path, lines))
        findings.extend(self._check_max_file_lines(file_path, lines))
        findings.extend(self._check_complexity(file_path, lines))
        findings.extend(self._check_no_trailing_spaces(file_path, lines))
        findings.extend(self._check_max_line_length(file_path, lines))
        return findings

    # ------------------------------------------------------------------
    # Bug / Security rules
    # ------------------------------------------------------------------

    def _check_no_eval(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """js.no-eval: direct use of eval()."""
        if not self._is_rule_enabled("js.no-eval"):
            return []
        findings: List[JSFinding] = []
        pattern = re.compile(r"\beval\s*\(")
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="js.no-eval",
                    category=JSRuleCategory.SECURITY,
                    severity=JSSeverity.ERROR,
                    title="Use of eval()",
                    description="eval() executes arbitrary code and is a security risk.",
                    code_snippet=line,
                    fix_suggestion="Remove eval() and use a safer alternative such as JSON.parse() or Function.",
                ))
        return findings

    def _check_no_implied_eval(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """js.no-implied-eval: setTimeout/setInterval with string literal."""
        if not self._is_rule_enabled("js.no-implied-eval"):
            return []
        findings: List[JSFinding] = []
        pattern = re.compile(r"(setTimeout|setInterval)\s*\(\s*['\"]")
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="js.no-implied-eval",
                    category=JSRuleCategory.SECURITY,
                    severity=JSSeverity.WARNING,
                    title="Implied eval via setTimeout/setInterval with string",
                    description="Passing a string to setTimeout or setInterval evaluates code like eval().",
                    code_snippet=line,
                    fix_suggestion="Pass a function reference instead of a string.",
                ))
        return findings

    def _check_no_debugger(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """js.no-debugger: debugger; statement."""
        if not self._is_rule_enabled("js.no-debugger"):
            return []
        findings: List[JSFinding] = []
        pattern = re.compile(r"\bdebugger\s*;")
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="js.no-debugger",
                    category=JSRuleCategory.BUG,
                    severity=JSSeverity.WARNING,
                    title="Debugger statement found",
                    description="debugger statements should be removed before committing code.",
                    code_snippet=line,
                    fix_suggestion="Remove the debugger statement.",
                ))
        return findings

    def _check_eqeqeq(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """js.eqeqeq: use of == or != instead of === or !==."""
        if not self._is_rule_enabled("js.eqeqeq"):
            return []
        findings: List[JSFinding] = []
        eq_pattern = re.compile(r"[^=!<>]==[^=]")
        neq_pattern = re.compile(r"[^!]!=[^=]")
        for idx, line in enumerate(lines, start=1):
            if eq_pattern.search(line) or neq_pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="js.eqeqeq",
                    category=JSRuleCategory.BUG,
                    severity=JSSeverity.WARNING,
                    title="Use === and !== instead of == and !=",
                    description="Loose equality operators perform type coercion and can produce unexpected results.",
                    code_snippet=line,
                    fix_suggestion="Replace == with === and != with !==.",
                ))
        return findings

    def _check_no_alert(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """js.no-alert: use of alert()."""
        if not self._is_rule_enabled("js.no-alert"):
            return []
        findings: List[JSFinding] = []
        pattern = re.compile(r"\balert\s*\(")
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="js.no-alert",
                    category=JSRuleCategory.CODE_SMELL,
                    severity=JSSeverity.WARNING,
                    title="Use of alert()",
                    description="alert() is a UI blocking call that should not be used in production code.",
                    code_snippet=line,
                    fix_suggestion="Remove alert() and use a proper notification mechanism.",
                ))
        return findings

    # ------------------------------------------------------------------
    # Code smell rules
    # ------------------------------------------------------------------

    def _check_no_var(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """js.no-var: use of var instead of let/const."""
        if not self._is_rule_enabled("js.no-var"):
            return []
        findings: List[JSFinding] = []
        pattern = re.compile(r"\bvar\s+")
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="js.no-var",
                    category=JSRuleCategory.CODE_SMELL,
                    severity=JSSeverity.WARNING,
                    title="Use let or const instead of var",
                    description="var has function scope and hoisting behavior that can cause subtle bugs.",
                    code_snippet=line,
                    fix_suggestion="Replace var with const (preferred) or let.",
                ))
        return findings

    def _check_no_empty_block(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """js.no-empty-block: empty block {}."""
        if not self._is_rule_enabled("js.no-empty-block"):
            return []
        findings: List[JSFinding] = []
        pattern = re.compile(r"\{\s*\}")
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="js.no-empty-block",
                    category=JSRuleCategory.CODE_SMELL,
                    severity=JSSeverity.INFO,
                    title="Empty block statement",
                    description="Empty blocks are likely unintentional and may hide incomplete logic.",
                    code_snippet=line,
                    fix_suggestion="Add a comment or implement the block body.",
                ))
        return findings

    def _check_no_console(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """js.no-console: use of console.log/warn/error/debug."""
        if not self._is_rule_enabled("js.no-console"):
            return []
        findings: List[JSFinding] = []
        pattern = re.compile(r"console\.(log|warn|error|debug)\s*\(")
        for idx, line in enumerate(lines, start=1):
            match = pattern.search(line)
            if match:
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="js.no-console",
                    category=JSRuleCategory.CODE_SMELL,
                    severity=JSSeverity.INFO,
                    title=f"Use of console.{match.group(1)}()",
                    description="Console logging should be removed or replaced with a proper logger in production.",
                    code_snippet=line,
                    fix_suggestion="Remove or replace with a structured logging library.",
                ))
        return findings

    def _check_max_file_lines(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """js.max-file-lines: file exceeds configured maximum line count."""
        if not self._is_rule_enabled("js.max-file-lines"):
            return []
        count = len(lines)
        if count > self._config.max_file_lines:
            return [_make_finding(
                file_path=file_path,
                line_number=1,
                rule_id="js.max-file-lines",
                category=JSRuleCategory.CODE_SMELL,
                severity=JSSeverity.WARNING,
                title=f"File exceeds {self._config.max_file_lines} lines ({count} lines)",
                description=(
                    f"This file has {count} lines which exceeds the configured maximum of "
                    f"{self._config.max_file_lines}. Large files are harder to maintain."
                ),
                fix_suggestion="Split the file into smaller, more focused modules.",
            )]
        return []

    # ------------------------------------------------------------------
    # Complexity rules
    # ------------------------------------------------------------------

    def _check_complexity(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """js.complexity: file-level cyclomatic complexity heuristic."""
        if not self._is_rule_enabled("js.complexity"):
            return []
        source = "\n".join(lines)
        decision_keywords = [
            r"\bif\b",
            r"\belse if\b",
            r"\bfor\b",
            r"\bwhile\b",
            r"\bcase\b",
            r"\bcatch\b",
            r"&&",
            r"\|\|",
            r"\?",
        ]
        total = sum(len(re.findall(kw, source)) for kw in decision_keywords)
        threshold = self._config.max_complexity * 5
        if total > threshold:
            return [_make_finding(
                file_path=file_path,
                line_number=1,
                rule_id="js.complexity",
                category=JSRuleCategory.COMPLEXITY,
                severity=JSSeverity.WARNING,
                title=f"High file-level complexity (score: {total})",
                description=(
                    f"The file has an estimated complexity score of {total} which exceeds "
                    f"the threshold of {threshold} (max_complexity={self._config.max_complexity} * 5). "
                    "Consider splitting complex logic into smaller functions."
                ),
                fix_suggestion="Extract complex logic into well-named helper functions.",
            )]
        return []

    # ------------------------------------------------------------------
    # Style rules
    # ------------------------------------------------------------------

    def _check_no_trailing_spaces(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """js.no-trailing-spaces: lines with trailing whitespace."""
        if not self._is_rule_enabled("js.no-trailing-spaces"):
            return []
        findings: List[JSFinding] = []
        pattern = re.compile(r"\s+$")
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="js.no-trailing-spaces",
                    category=JSRuleCategory.STYLE,
                    severity=JSSeverity.INFO,
                    title="Trailing whitespace",
                    description="This line has trailing whitespace characters.",
                    code_snippet=line,
                    fix_suggestion="Remove trailing whitespace.",
                ))
        return findings

    def _check_max_line_length(self, file_path: str, lines: List[str]) -> List[JSFinding]:
        """js.max-line-length: lines exceeding 120 characters."""
        if not self._is_rule_enabled("js.max-line-length"):
            return []
        findings: List[JSFinding] = []
        for idx, line in enumerate(lines, start=1):
            if len(line) > 120:
                findings.append(_make_finding(
                    file_path=file_path,
                    line_number=idx,
                    rule_id="js.max-line-length",
                    category=JSRuleCategory.STYLE,
                    severity=JSSeverity.INFO,
                    title=f"Line exceeds 120 characters ({len(line)} chars)",
                    description=f"This line is {len(line)} characters long, exceeding the 120-character limit.",
                    code_snippet=line[:120] + "...",
                    fix_suggestion="Break the line into shorter segments.",
                ))
        return findings
