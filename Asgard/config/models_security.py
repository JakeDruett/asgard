"""
Asgard Configuration Models - Security and Infrastructure

Security-related configuration models and the unified AsgardConfig container.
"""

from typing import List, cast

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from Asgard.config._models_volundr import (
    CICDConfig,
    DockerConfig,
    KubernetesConfig,
    TerraformConfig,
    VolundrConfig,
)
from Asgard.config.models_base import GlobalConfig
from Asgard.config.models_quality import (
    ForsetiConfig,
    FreyaConfig,
    HeimdallQualityConfig,
)


class HeimdallSecurityConfig(BaseModel):
    """Configuration for Heimdall security analysis."""
    model_config = {"use_enum_values": True}

    enable_bandit: bool = Field(default=True, description="Enable Bandit security scanner")
    bandit_severity: str = Field(default="low", description="Minimum Bandit severity to report")
    bandit_confidence: str = Field(default="low", description="Minimum Bandit confidence to report")
    check_hardcoded_secrets: bool = Field(default=True, description="Check for hardcoded secrets")
    check_sql_injection: bool = Field(default=True, description="Check for SQL injection vulnerabilities")
    check_xss: bool = Field(default=True, description="Check for XSS vulnerabilities")
    check_path_traversal: bool = Field(default=True, description="Check for path traversal vulnerabilities")


class HeimdallConfig(BaseModel):
    """Complete Heimdall configuration."""
    model_config = {"use_enum_values": True}

    quality: HeimdallQualityConfig = Field(
        default_factory=HeimdallQualityConfig,
        description="Quality analysis configuration"
    )
    security: HeimdallSecurityConfig = Field(
        default_factory=HeimdallSecurityConfig,
        description="Security analysis configuration"
    )
    include_tests: bool = Field(default=False, description="Include test files in analysis")
    fail_on_error: bool = Field(default=True, description="Exit with error code if issues found")


class WebVitalsConfig(BaseModel):
    """Web Vitals thresholds configuration for Verdandi."""
    model_config = {"use_enum_values": True}

    lcp_threshold_ms: int = Field(default=2500, description="LCP threshold (ms)", ge=100, le=30000)
    fid_threshold_ms: int = Field(default=100, description="FID threshold (ms)", ge=10, le=5000)
    cls_threshold: float = Field(default=0.1, description="CLS threshold", ge=0.0, le=1.0)
    fcp_threshold_ms: int = Field(default=1800, description="FCP threshold (ms)", ge=100, le=30000)
    ttfb_threshold_ms: int = Field(default=800, description="TTFB threshold (ms)", ge=50, le=10000)
    inp_threshold_ms: int = Field(default=200, description="INP threshold (ms)", ge=10, le=5000)
    track_long_tasks: bool = Field(default=True, description="Track long-running JavaScript tasks")
    long_task_threshold_ms: int = Field(default=50, description="Long task threshold (ms)", ge=10, le=1000)


class APDEXConfig(BaseModel):
    """APDEX (Application Performance Index) configuration."""
    model_config = {"use_enum_values": True}

    enabled: bool = Field(default=True, description="Enable APDEX calculation")
    satisfied_threshold_ms: int = Field(default=500, description="Satisfied threshold (ms)", ge=50, le=30000)
    tolerating_threshold_ms: int = Field(default=2000, description="Tolerating threshold (ms)", ge=100, le=60000)
    target_score: float = Field(default=0.85, description="Target APDEX score (0.0-1.0)", ge=0.0, le=1.0)


class VerdandiConfig(BaseModel):
    """Configuration for Verdandi performance metrics module."""
    model_config = {"use_enum_values": True}

    enable_profiling: bool = Field(default=True, description="Enable code profiling")
    profile_depth: int = Field(default=10, description="Call stack depth for profiling", ge=1, le=100)
    sample_rate: float = Field(default=1.0, description="Sampling rate (0.0-1.0)", ge=0.01, le=1.0)
    apdex: APDEXConfig = Field(default_factory=APDEXConfig, description="APDEX configuration")
    apdex_threshold_ms: int = Field(
        default=500, description="APDEX threshold (ms, deprecated)", ge=50, le=30000
    )
    sla_percentile: float = Field(default=95.0, description="SLA percentile", ge=50.0, le=99.99)
    sla_response_time_ms: int = Field(default=1000, description="SLA response time (ms)", ge=50, le=60000)
    memory_threshold_mb: float = Field(default=100.0, description="Memory warning threshold (MB)", ge=1.0)
    cpu_threshold_percent: float = Field(default=80.0, description="CPU warning threshold", ge=1.0, le=100.0)
    response_time_threshold_ms: float = Field(default=1000.0, description="Response time warning (ms)", ge=1.0)
    cache_hit_rate_threshold: float = Field(default=0.8, description="Min cache hit rate", ge=0.0, le=1.0)
    track_cache_metrics: bool = Field(default=True, description="Track cache hit/miss metrics")
    web_vitals: WebVitalsConfig = Field(
        default_factory=WebVitalsConfig, description="Web Vitals thresholds"
    )
    generate_flamegraphs: bool = Field(default=False, description="Generate flamegraph visualizations")
    flamegraph_output_path: str = Field(default=".verdandi/flamegraphs", description="Flamegraph output path")
    retain_metrics_days: int = Field(default=30, description="Days to retain metrics", ge=1, le=365)
    baseline_comparison: bool = Field(default=True, description="Enable baseline comparison")


class AsgardConfig(BaseModel):
    """Unified Asgard configuration container."""
    model_config = {
        "use_enum_values": True,
        "populate_by_name": True,
    }

    version: str = Field(default="1.0.0", description="Configuration schema version")
    global_config: GlobalConfig = Field(
        default_factory=GlobalConfig, alias="global", description="Global configuration"
    )
    heimdall: HeimdallConfig = Field(default_factory=HeimdallConfig, description="Heimdall configuration")
    forseti: ForsetiConfig = Field(default_factory=ForsetiConfig, description="Forseti configuration")
    freya: FreyaConfig = Field(default_factory=FreyaConfig, description="Freya configuration")
    verdandi: VerdandiConfig = Field(default_factory=VerdandiConfig, description="Verdandi configuration")
    volundr: VolundrConfig = Field(default_factory=VolundrConfig, description="Volundr configuration")

    def to_yaml(self) -> str:
        """Export configuration as YAML string."""
        data = self.model_dump(by_alias=True)
        return cast(str, yaml.dump(data, default_flow_style=False, sort_keys=False))

    def to_toml(self) -> str:
        """Export configuration as TOML string for pyproject.toml."""
        lines = ["[tool.asgard]"]
        data = self.model_dump(by_alias=True)
        lines.extend(self._dict_to_toml(data, "tool.asgard"))
        return "\n".join(lines)

    def _dict_to_toml(self, data: dict, prefix: str, indent: int = 0) -> List[str]:
        """Convert dictionary to TOML format lines."""
        lines = []
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                lines.append(f"\n[{full_key}]")
                for k, v in value.items():
                    if isinstance(v, dict):
                        lines.extend(self._dict_to_toml({k: v}, full_key))
                    elif isinstance(v, list):
                        lines.append(f"{k} = {self._to_toml_value(v)}")
                    else:
                        lines.append(f"{k} = {self._to_toml_value(v)}")
            elif not prefix.endswith("tool.asgard"):
                lines.append(f"{key} = {self._to_toml_value(value)}")
        return lines

    def _to_toml_value(self, value) -> str:
        """Convert Python value to TOML representation."""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, list):
            items = [self._to_toml_value(v) for v in value]
            return f"[{', '.join(items)}]"
        elif value is None:
            return '""'
        return str(value)
