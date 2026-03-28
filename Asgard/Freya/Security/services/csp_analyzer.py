"""Freya CSP Analyzer - deep analysis of Content-Security-Policy headers."""

import re
from typing import List, Optional

from Asgard.Freya.Security.models.security_header_models import (
    CSPDirective,
    CSPReport,
    SecurityConfig,
)
from Asgard.Freya.Security.services._csp_analyzer_helpers import (
    analyze_issues,
    calculate_score,
)


class CSPAnalyzer:
    """Analyzes Content-Security-Policy headers for security issues."""

    FETCH_DIRECTIVES = [
        "default-src", "script-src", "script-src-elem", "script-src-attr",
        "style-src", "style-src-elem", "style-src-attr", "img-src",
        "font-src", "connect-src", "media-src", "object-src",
        "prefetch-src", "child-src", "frame-src", "worker-src", "manifest-src",
    ]
    DOCUMENT_DIRECTIVES = ["base-uri", "plugin-types", "sandbox"]
    NAVIGATION_DIRECTIVES = ["form-action", "frame-ancestors", "navigate-to"]
    REPORTING_DIRECTIVES = ["report-uri", "report-to"]
    UNSAFE_KEYWORDS = ["'unsafe-inline'", "'unsafe-eval'", "'unsafe-hashes'"]

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()

    def analyze(self, csp_value: str) -> CSPReport:
        """Analyze a CSP header value and return CSPReport."""
        report = CSPReport(raw_value=csp_value, is_present=True)

        directives = self._parse_directives(csp_value)
        report.directives = directives

        directive_map = {d.name: d for d in directives}
        report.default_src = directive_map.get("default-src")
        report.script_src = directive_map.get("script-src")
        report.style_src = directive_map.get("style-src")
        report.img_src = directive_map.get("img-src")
        report.connect_src = directive_map.get("connect-src")
        report.frame_src = directive_map.get("frame-src")
        report.font_src = directive_map.get("font-src")
        report.object_src = directive_map.get("object-src")
        report.base_uri = directive_map.get("base-uri")
        report.form_action = directive_map.get("form-action")
        report.frame_ancestors = directive_map.get("frame-ancestors")

        report.uses_nonces = self._uses_nonces(csp_value)
        report.uses_hashes = self._uses_hashes(csp_value)
        report.uses_strict_dynamic = "'strict-dynamic'" in csp_value

        analyze_issues(report, self.config.allow_unsafe_eval)
        report.security_score = calculate_score(report)

        return report

    def _parse_directives(self, csp_value: str) -> List[CSPDirective]:
        """Parse CSP value into directives."""
        directives = []
        parts = csp_value.split(";")

        for part in parts:
            part = part.strip()
            if not part:
                continue

            tokens = part.split()
            if not tokens:
                continue

            directive_name = tokens[0].lower()
            values = tokens[1:] if len(tokens) > 1 else []
            directive = CSPDirective(name=directive_name, values=values)

            for val in values:
                val_lower = val.lower()
                if val_lower == "'unsafe-inline'":
                    directive.has_unsafe_inline = True
                elif val_lower == "'unsafe-eval'":
                    directive.has_unsafe_eval = True
                elif val == "*":
                    directive.allows_any = True

            directives.append(directive)

        return directives

    def _uses_nonces(self, csp_value: str) -> bool:
        """Check if CSP uses nonces."""
        return bool(re.search(r"'nonce-[^']+?'", csp_value))

    def _uses_hashes(self, csp_value: str) -> bool:
        """Check if CSP uses hashes."""
        return bool(re.search(r"'sha(256|384|512)-[^']+?'", csp_value))

    def get_sample_policy(self, strict: bool = True) -> str:
        """Generate a sample CSP policy."""
        if strict:
            return (
                "default-src 'self'; "
                "script-src 'self' 'strict-dynamic' 'nonce-{RANDOM}'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'self'; "
                "upgrade-insecure-requests"
            )
        else:
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "object-src 'none'; "
                "frame-ancestors 'self'"
            )
