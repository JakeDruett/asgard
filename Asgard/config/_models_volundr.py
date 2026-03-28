"""
Asgard Configuration Models - Volundr Infrastructure

Volundr-specific configuration models for Kubernetes, Docker, Terraform, and CI/CD.
"""

from typing import Dict, List, Literal

from pydantic import BaseModel, Field, model_validator

from Asgard.config.models_base import CICDPlatform, TerraformBackend


class KubernetesConfig(BaseModel):
    """Kubernetes-specific configuration for Volundr."""
    model_config = {"use_enum_values": True}

    version: str = Field(default="1.28", description="Target Kubernetes version")
    namespace: str = Field(default="default", description="Default Kubernetes namespace")
    enable_network_policies: bool = Field(default=True, description="Generate network policies")
    enable_pod_security: bool = Field(default=True, description="Enable Pod Security Standards")
    pod_security_level: Literal["privileged", "baseline", "restricted"] = Field(
        default="baseline",
        description="Pod Security Standard level"
    )
    resource_quotas_enabled: bool = Field(default=False, description="Generate resource quotas")
    default_replicas: int = Field(default=1, description="Default number of replicas", ge=1, le=100)
    enable_hpa: bool = Field(default=False, description="Enable Horizontal Pod Autoscaler generation")
    hpa_min_replicas: int = Field(default=1, description="HPA minimum replicas", ge=1)
    hpa_max_replicas: int = Field(default=10, description="HPA maximum replicas", ge=1, le=1000)


class DockerConfig(BaseModel):
    """Docker-specific configuration for Volundr."""
    model_config = {"use_enum_values": True}

    default_registry: str = Field(default="", description="Default Docker registry URL")
    base_image: str = Field(default="python:3.11-slim", description="Default base image for Python projects")
    enable_multi_stage: bool = Field(default=True, description="Use multi-stage builds")
    enable_buildkit: bool = Field(default=True, description="Enable BuildKit features")
    cache_from: List[str] = Field(default_factory=list, description="Images to use as cache sources")
    labels: Dict[str, str] = Field(default_factory=dict, description="Default labels to add to images")
    security_scan_enabled: bool = Field(default=True, description="Enable security scanning in generated configs")


class TerraformConfig(BaseModel):
    """Terraform-specific configuration for Volundr."""
    model_config = {"use_enum_values": True}

    backend: TerraformBackend = Field(default=TerraformBackend.LOCAL, description="Terraform backend type")
    backend_config: Dict[str, str] = Field(
        default_factory=dict,
        description="Backend-specific configuration options"
    )
    version_constraint: str = Field(default=">= 1.5.0", description="Terraform version constraint")
    provider_versions: Dict[str, str] = Field(
        default_factory=lambda: {
            "aws": "~> 5.0",
            "google": "~> 5.0",
            "azurerm": "~> 3.0",
            "kubernetes": "~> 2.0",
        },
        description="Provider version constraints"
    )
    enable_state_locking: bool = Field(default=True, description="Enable state locking")
    workspace_prefix: str = Field(default="", description="Prefix for Terraform workspaces")


class CICDConfig(BaseModel):
    """CI/CD configuration for Volundr."""
    model_config = {"use_enum_values": True}

    platform: CICDPlatform = Field(default=CICDPlatform.GITHUB_ACTIONS, description="CI/CD platform")
    enable_caching: bool = Field(default=True, description="Enable dependency caching in pipelines")
    parallel_jobs: int = Field(default=4, description="Number of parallel jobs", ge=1, le=50)
    timeout_minutes: int = Field(default=30, description="Default job timeout in minutes", ge=5, le=360)
    enable_security_scans: bool = Field(default=True, description="Include security scanning steps")
    enable_lint_checks: bool = Field(default=True, description="Include linting steps")
    enable_test_coverage: bool = Field(default=True, description="Include test coverage reporting")
    artifact_retention_days: int = Field(default=30, description="Days to retain build artifacts", ge=1, le=90)


class VolundrConfig(BaseModel):
    """Configuration for Volundr infrastructure generation module."""
    model_config = {"use_enum_values": True}

    templates_path: str = Field(default="", description="Custom templates path")
    output_path: str = Field(default=".volundr/generated", description="Path for generated files")
    dry_run: bool = Field(default=False, description="Generate without writing files")
    docker: DockerConfig = Field(default_factory=DockerConfig, description="Docker configuration")
    default_registry: str = Field(
        default="",
        description="Default Docker registry (deprecated, use docker.default_registry)"
    )
    kubernetes: KubernetesConfig = Field(
        default_factory=KubernetesConfig,
        description="Kubernetes configuration"
    )
    kubernetes_version: str = Field(
        default="1.28",
        description="Target Kubernetes version (deprecated, use kubernetes.version)"
    )
    kubernetes_namespace: str = Field(
        default="default",
        description="Kubernetes namespace (deprecated, use kubernetes.namespace)"
    )
    helm_chart_version: str = Field(default="0.1.0", description="Default Helm chart version")
    helm_repository: str = Field(default="", description="Default Helm repository URL")
    enable_helm_generation: bool = Field(default=True, description="Generate Helm charts")
    terraform: TerraformConfig = Field(
        default_factory=TerraformConfig,
        description="Terraform configuration"
    )
    terraform_backend: TerraformBackend = Field(
        default=TerraformBackend.LOCAL,
        description="Terraform backend (deprecated, use terraform.backend)"
    )
    cicd: CICDConfig = Field(default_factory=CICDConfig, description="CI/CD configuration")
    cicd_platform: CICDPlatform = Field(
        default=CICDPlatform.GITHUB_ACTIONS,
        description="CI/CD platform (deprecated, use cicd.platform)"
    )
    validate_generated: bool = Field(default=True, description="Validate generated configurations")
    fail_on_validation_error: bool = Field(default=True, description="Fail if validation errors occur")

    @model_validator(mode="after")
    def sync_legacy_fields(self) -> "VolundrConfig":
        """Sync legacy fields with nested configs for backwards compatibility."""
        if self.default_registry and not self.docker.default_registry:
            self.docker.default_registry = self.default_registry
        elif self.docker.default_registry:
            self.default_registry = self.docker.default_registry

        if self.kubernetes_version != "1.28" and self.kubernetes.version == "1.28":
            self.kubernetes.version = self.kubernetes_version
        elif self.kubernetes.version != "1.28":
            self.kubernetes_version = self.kubernetes.version

        if self.kubernetes_namespace != "default" and self.kubernetes.namespace == "default":
            self.kubernetes.namespace = self.kubernetes_namespace
        elif self.kubernetes.namespace != "default":
            self.kubernetes_namespace = self.kubernetes.namespace

        if self.terraform_backend != TerraformBackend.LOCAL and self.terraform.backend == TerraformBackend.LOCAL:
            self.terraform.backend = self.terraform_backend
        elif self.terraform.backend != TerraformBackend.LOCAL:
            self.terraform_backend = self.terraform.backend

        if self.cicd_platform != CICDPlatform.GITHUB_ACTIONS and self.cicd.platform == CICDPlatform.GITHUB_ACTIONS:
            self.cicd.platform = self.cicd_platform
        elif self.cicd.platform != CICDPlatform.GITHUB_ACTIONS:
            self.cicd_platform = self.cicd.platform

        return self
