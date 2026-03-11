"""TypeScript models package (re-exports from js_models with TS-specific additions)."""

from Asgard.Heimdall.Quality.languages.javascript.models.js_models import (
    JSAnalysisConfig,
    JSFinding,
    JSReport,
    JSRuleCategory,
    JSSeverity,
)

__all__ = [
    "JSAnalysisConfig",
    "JSFinding",
    "JSReport",
    "JSRuleCategory",
    "JSSeverity",
]
