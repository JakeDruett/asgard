"""HTML Report Generator - generates rich HTML reports with dashboards and charts."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from Asgard.Reporting._html_report_builders import build_quality_dashboard_content
from Asgard.Reporting._html_templates import REPORT_CSS, REPORT_JS


@dataclass
class ScoreCard:
    """Represents a dashboard score card."""
    title: str
    value: str
    label: str
    status: str = "good"  # good, warning, bad


class HTMLReportGenerator:
    """Generates rich HTML reports for Asgard analysis results."""

    def __init__(self, title: str = "Asgard Analysis Report"):
        self.title = title

    def _wrap_html(self, content: str, title: str) -> str:
        """Wrap content in complete HTML document."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{REPORT_CSS}</style>
</head>
<body>
    <div class="container">
        {content}
    </div>
    <script>{REPORT_JS}</script>
</body>
</html>"""

    def _generate_header(self, subtitle: str = "") -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subtitle_html = f"<div class='meta'>{subtitle}</div>" if subtitle else ""
        return f"""
<header>
    <h1>{self.title}</h1>
    {subtitle_html}
    <div class='meta'>Generated: {timestamp}</div>
</header>"""

    def _generate_score_card(self, card: ScoreCard) -> str:
        """Generate a single score card."""
        return f"""
<div class="card">
    <h2>{card.title}</h2>
    <div class="score {card.status}">{card.value}</div>
    <div class="label">{card.label}</div>
</div>"""

    def _generate_dashboard(self, cards: List[ScoreCard]) -> str:
        """Generate dashboard with score cards."""
        cards_html = "\n".join(self._generate_score_card(card) for card in cards)
        return f"""
<div class="dashboard">
    {cards_html}
</div>"""

    def _generate_table(self, headers: List[str], rows: List[List[str]], title: str = "") -> str:
        """Generate an HTML table."""
        header_html = "".join(f"<th>{h}</th>" for h in headers)
        rows_html = "\n".join(
            "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
            for row in rows
        )
        title_html = f"<h2>{title}</h2>" if title else ""
        return f"""
<div class="section">
    {title_html}
    <table>
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
</div>"""

    def _generate_severity_badge(self, severity: str) -> str:
        """Generate a severity badge."""
        severity_lower = severity.lower()
        return f'<span class="severity-badge severity-{severity_lower}">{severity}</span>'

    def _generate_code_block(
        self, code: str, highlight_line: Optional[int] = None, start_line: int = 1,
    ) -> str:
        """Generate a code block with optional line highlighting."""
        lines_html = []
        for i, line in enumerate(code.split("\n"), start=start_line):
            line_class = "highlight" if i == highlight_line else ""
            escaped_line = line.replace("<", "&lt;").replace(">", "&gt;")
            lines_html.append(
                f'<span class="{line_class}"><span class="line-number">{i:4d}</span>{escaped_line}</span>'
            )
        return f"""
<div class="code-block">
    <pre>{"".join(lines_html)}</pre>
</div>"""

    def _generate_file_list(self, files: List[tuple], title: str = "Files") -> str:
        """Generate a file list with counts."""
        items_html = "\n".join(
            f'<li><span class="file-path">{path}</span><span class="badge-count">{count}</span></li>'
            for path, count in files
        )
        return f"""
<div class="section">
    <h2>{title}</h2>
    <ul class="file-list">
        {items_html}
    </ul>
</div>"""

    def _generate_progress_bar(self, value: float, max_value: float = 100, label: str = "") -> str:
        """Generate a progress bar."""
        percentage = min(100, (value / max_value) * 100) if max_value > 0 else 0
        status = "good" if percentage >= 80 else "warning" if percentage >= 50 else "bad"
        return f"""
<div>
    <span>{label}: {value:.1f}%</span>
    <div class="progress-bar">
        <div class="fill {status}" style="width: {percentage}%"></div>
    </div>
</div>"""

    def generate_typing_report(self, report) -> str:
        """Generate HTML report for typing coverage analysis."""
        coverage_status = "good" if report.coverage_percentage >= 80 else \
                         "warning" if report.coverage_percentage >= 50 else "bad"

        cards = [
            ScoreCard("Type Coverage", f"{report.coverage_percentage:.1f}%",
                      f"Threshold: {report.threshold:.1f}%", coverage_status),
            ScoreCard("Functions", str(report.total_functions), "Total analyzed", "good"),
            ScoreCard("Fully Typed", str(report.fully_annotated),
                      f"{report.fully_annotated / max(1, report.total_functions) * 100:.0f}% of total",
                      "good" if report.fully_annotated == report.total_functions else "warning"),
            ScoreCard("Status", "PASS" if report.is_passing else "FAIL",
                      f"Files: {report.files_scanned}",
                      "good" if report.is_passing else "bad"),
        ]

        file_rows = []
        for f in sorted(report.files_analyzed, key=lambda x: x.coverage_percentage)[:20]:
            coverage_badge = self._generate_severity_badge(
                "good" if f.coverage_percentage >= 80 else
                "warning" if f.coverage_percentage >= 50 else "low"
            )
            file_rows.append([
                f.relative_path, str(f.total_functions), str(f.fully_annotated),
                f"{f.coverage_percentage:.1f}%", coverage_badge,
            ])

        file_table = self._generate_table(
            ["File", "Functions", "Typed", "Coverage", "Status"], file_rows,
            "File Coverage (Bottom 20)",
        )

        func_rows = []
        for func in report.unannotated_functions[:30]:
            missing = ", ".join(func.missing_parameter_names[:3])
            if len(func.missing_parameter_names) > 3:
                missing += "..."
            severity_badge = self._generate_severity_badge(
                func.severity if isinstance(func.severity, str) else func.severity.value
            )
            func_rows.append([
                func.relative_path, func.qualified_name, str(func.line_number),
                missing or "-", "Yes" if func.has_return_annotation else "No", severity_badge,
            ])

        func_table = self._generate_table(
            ["File", "Function", "Line", "Missing Params", "Has Return", "Severity"],
            func_rows, "Functions Needing Annotations",
        )

        content = f"""
{self._generate_header(f"Scan: {report.scan_path}")}
{self._generate_dashboard(cards)}
{file_table}
{func_table}
<footer>Generated by Asgard Heimdall</footer>
"""
        return self._wrap_html(content, f"Type Coverage - {self.title}")

    def generate_quality_dashboard(
        self,
        quality_result=None,
        complexity_result=None,
        smell_report=None,
        typing_report=None,
        datetime_report=None,
        forbidden_report=None,
    ) -> str:
        """Generate a unified quality dashboard HTML report."""
        return build_quality_dashboard_content(
            self, ScoreCard,
            quality_result, complexity_result, smell_report,
            typing_report, datetime_report, forbidden_report,
        )
