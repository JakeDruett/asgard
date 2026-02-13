# Asgard Module Expansion Plan

## Overview

This document outlines the plan to expand Freya, Forseti, Verdandi, and Volundr to match Heimdall's level of sophistication. Heimdall serves as the reference implementation with its:

- **163 Python files** across Quality, Security, OOP, Performance, Architecture, Coverage domains
- **Comprehensive CLI** with nested subparsers and consistent flags
- **Parallel processing** via ProcessPoolExecutor
- **Incremental scanning** with SHA-256 file hash caching
- **Baseline system** for suppressing known violations
- **Multiple output formats** (text, JSON, GitHub Actions)
- **Configuration integration** via unified AsgardConfig

---

## Current State Analysis

| Module | Files | CLI Commands | Services | Configuration | Parallel | Incremental | Baseline |
|--------|-------|--------------|----------|---------------|----------|-------------|----------|
| Heimdall | 163 | 20+ | 40+ | Yes | Yes | Yes | Yes |
| Freya | 41 | 12 | 15 | Partial | No | No | Partial |
| Forseti | 49 | 15 | 18 | No | No | No | No |
| Verdandi | 52 | 10 | 20 | No | No | No | No |
| Volundr | 24 | 8 | 10 | No | No | No | No |

---

## Phase 1: Common Infrastructure (All Modules)

### 1.1 Unified Base Classes

Create shared infrastructure that all modules can inherit:

```
Asgard/common/
    __init__.py
    parallel.py          # ParallelRunner base class
    incremental.py       # IncrementalCache base class
    baseline.py          # BaselineManager interface
    output_formatter.py  # UnifiedFormatter (text/json/github)
    progress.py          # ProgressReporter for CLI
```

**Tasks:**
- [ ] Extract Heimdall's parallel scanning into reusable `ParallelRunner` class
- [ ] Extract incremental scanning into reusable `IncrementalCache` class
- [ ] Create `UnifiedFormatter` that outputs text/json/github for any result type
- [ ] Create `ProgressReporter` with spinner and progress bar support

### 1.2 Configuration Integration

Extend `Asgard/config/models.py` to include all modules:

```python
class FreyaConfig(BaseModel):
    """Freya visual testing configuration."""
    default_viewport: Tuple[int, int] = (1920, 1080)
    diff_threshold: float = 0.1
    screenshot_format: str = "png"
    headless: bool = True
    timeout_ms: int = 30000
    accessibility: AccessibilityConfig = Field(default_factory=AccessibilityConfig)

class ForsetiConfig(BaseModel):
    """Forseti API validation configuration."""
    strict_mode: bool = False
    allow_deprecated: bool = True
    max_response_time_ms: int = 5000
    schema_cache_ttl: int = 3600

class VerdandiConfig(BaseModel):
    """Verdandi performance metrics configuration."""
    apdex_threshold_ms: float = 500.0
    sla_percentile: float = 95.0
    cache_hit_rate_threshold: float = 0.8
    web_vitals_thresholds: WebVitalsConfig = Field(default_factory=WebVitalsConfig)

class VolundrConfig(BaseModel):
    """Volundr infrastructure generation configuration."""
    default_registry: str = "docker.io"
    kubernetes_namespace: str = "default"
    terraform_backend: str = "local"
    cicd_platform: str = "github"
```

---

## Phase 2: Freya Enhancements

### Current Capabilities
- Accessibility auditing (WCAG, ARIA, color contrast, keyboard nav, screen reader)
- Visual regression testing (screenshot capture, comparison)
- Responsive testing (breakpoints, viewport, touch targets, mobile compatibility)
- Site crawling and unified testing

### 2.1 New Scanners

| Scanner | Purpose | Priority |
|---------|---------|----------|
| `PerformanceScanner` | Page load metrics, resource timing | High |
| `SEOScanner` | Meta tags, structured data, robots.txt | Medium |
| `SecurityHeaderScanner` | CSP, HSTS, X-Frame-Options | High |
| `LinkValidator` | Broken links, redirect chains | Medium |
| `ImageOptimizationScanner` | Alt text, lazy loading, format optimization | Medium |
| `ConsoleErrorScanner` | JavaScript errors and warnings | High |

**Files to Create:**
```
Freya/Performance/
    models/performance_models.py
    services/page_load_analyzer.py
    services/resource_timing_analyzer.py
    services/lighthouse_wrapper.py

Freya/SEO/
    models/seo_models.py
    services/meta_tag_analyzer.py
    services/structured_data_validator.py
    services/robots_analyzer.py

Freya/Security/
    models/security_header_models.py
    services/security_header_scanner.py
    services/csp_analyzer.py
```

### 2.2 CLI Enhancements

Add new commands:
```bash
freya performance audit <url>      # Full performance audit
freya performance load-time <url>  # Page load timing
freya performance resources <url>  # Resource analysis

freya seo audit <url>              # Full SEO audit
freya seo meta <url>               # Meta tag analysis
freya seo structured-data <url>    # Schema.org validation

freya security headers <url>       # Security header check
freya security csp <url>           # CSP policy analysis

freya links validate <url>         # Broken link detection
freya images audit <url>           # Image optimization check
freya console errors <url>         # JavaScript error capture
```

Add common flags:
```
--parallel / -P                    Enable parallel URL processing
--incremental / -I                 Only retest changed pages
--baseline <path>                  Filter against baseline
--format text|json|github          Output format
--output <dir>                     Output directory for reports
```

### 2.3 Enhanced Reporting

- HTML report dashboard with:
  - Overall site health score
  - Accessibility score breakdown
  - Performance score
  - Visual regression diff viewer
  - Page-by-page results
- JSON export for CI integration
- GitHub Actions annotations

### 2.4 Parallel and Incremental Support

- Parallel URL testing with configurable concurrency
- Incremental testing: hash page content, only retest changed pages
- Baseline management for known accessibility issues

---

## Phase 3: Forseti Enhancements

### Current Capabilities
- OpenAPI validation, generation, conversion
- GraphQL schema validation, generation, introspection
- JSON Schema validation, inference
- Database schema analysis, diff, migration generation
- Contract compatibility checking, breaking change detection

### 3.1 New Validators

| Validator | Purpose | Priority |
|-----------|---------|----------|
| `AsyncAPIValidator` | Event-driven API validation | Medium |
| `ProtobufValidator` | Protocol Buffer schema validation | Medium |
| `AvroValidator` | Avro schema validation | Low |
| `MockServerGenerator` | Generate mock servers from specs | High |
| `SDKGenerator` | Generate client SDKs from specs | High |
| `DocumentationGenerator` | Generate API docs from specs | Medium |

**Files to Create:**
```
Forseti/AsyncAPI/
    models/asyncapi_models.py
    services/asyncapi_validator_service.py
    services/asyncapi_parser_service.py

Forseti/MockServer/
    models/mock_models.py
    services/mock_server_generator.py
    services/mock_data_generator.py

Forseti/CodeGen/
    models/codegen_models.py
    services/typescript_generator.py
    services/python_generator.py
    services/golang_generator.py
```

### 3.2 CLI Enhancements

Add new commands:
```bash
forseti asyncapi validate <spec>   # Validate AsyncAPI spec
forseti asyncapi convert <spec>    # Convert between versions

forseti mock generate <spec>       # Generate mock server
forseti mock serve <spec>          # Run mock server

forseti codegen typescript <spec>  # Generate TypeScript client
forseti codegen python <spec>      # Generate Python client
forseti codegen golang <spec>      # Generate Go client

forseti docs generate <spec>       # Generate API documentation
```

Add common flags:
```
--format text|json|github          Output format
--strict                           Enable strict validation
--baseline <path>                  Filter against baseline
```

### 3.3 Breaking Change Detection Enhancements

- Semantic versioning suggestion based on changes
- Detailed impact analysis
- Migration path suggestions
- Backwards compatibility scoring

### 3.4 CI/CD Integration

- GitHub Actions annotation output
- Pre-commit hook integration
- API changelog generation

---

## Phase 4: Verdandi Enhancements

### Current Capabilities
- Web vitals (LCP, FID, CLS, INP, TTFB, FCP)
- Percentile analysis
- Apdex scoring
- SLA compliance checking
- Cache metrics

### 4.1 New Analyzers

| Analyzer | Purpose | Priority |
|----------|---------|----------|
| `APMAnalyzer` | Application performance monitoring | High |
| `TracingAnalyzer` | Distributed tracing analysis | High |
| `ErrorBudgetCalculator` | SLO/SLI error budget tracking | High |
| `CapacityPlanner` | Capacity planning from metrics | Medium |
| `AnomalyDetector` | Performance anomaly detection | Medium |
| `RegressionDetector` | Performance regression detection | High |

**Files to Create:**
```
Verdandi/APM/
    models/apm_models.py
    services/span_analyzer.py
    services/trace_aggregator.py
    services/service_map_builder.py

Verdandi/SLO/
    models/slo_models.py
    services/error_budget_calculator.py
    services/sli_tracker.py
    services/burn_rate_analyzer.py

Verdandi/Anomaly/
    models/anomaly_models.py
    services/statistical_detector.py
    services/baseline_comparator.py
    services/regression_detector.py
```

### 4.2 CLI Enhancements

Add new commands:
```bash
verdandi apm analyze <traces>      # Analyze APM traces
verdandi apm service-map <traces>  # Generate service dependency map

verdandi slo calculate <metrics>   # Calculate SLO compliance
verdandi slo error-budget <metrics> # Calculate error budget
verdandi slo burn-rate <metrics>   # Analyze burn rate

verdandi anomaly detect <data>     # Detect anomalies in metrics
verdandi regression check <before> <after>  # Check for regressions

verdandi report generate <metrics> # Generate performance report
verdandi report trend <metrics>    # Generate trend analysis
```

Add common flags:
```
--format text|json|github|html     Output format
--window <duration>                Time window for analysis
--threshold <value>                Custom threshold
--baseline <path>                  Compare against baseline
```

### 4.3 Data Source Integration

- Prometheus metric import
- Jaeger trace import
- OpenTelemetry support
- Custom metric ingestion

### 4.4 Visualization

- ASCII histograms for terminal output
- HTML reports with interactive charts
- Service dependency visualization

---

## Phase 5: Volundr Enhancements

### Current Capabilities
- Kubernetes manifest generation
- Dockerfile generation
- Docker Compose generation
- Terraform configuration generation
- CI/CD pipeline generation
- Health probe utilities

### 5.1 New Generators

| Generator | Purpose | Priority |
|-----------|---------|----------|
| `HelmChartGenerator` | Helm chart scaffolding | High |
| `KustomizeGenerator` | Kustomize overlays | High |
| `ArgoAppGenerator` | ArgoCD Application manifests | Medium |
| `TektonPipelineGenerator` | Tekton pipeline generation | Medium |
| `PulumiGenerator` | Pulumi infrastructure code | Low |
| `AnsiblePlaybookGenerator` | Ansible playbook generation | Low |

**Files to Create:**
```
Volundr/Helm/
    models/helm_models.py
    services/chart_generator.py
    services/values_generator.py
    templates/

Volundr/Kustomize/
    models/kustomize_models.py
    services/overlay_generator.py
    services/patch_generator.py

Volundr/GitOps/
    models/gitops_models.py
    services/argocd_generator.py
    services/flux_generator.py
```

### 5.2 CLI Enhancements

Add new commands:
```bash
volundr helm init <name>           # Initialize Helm chart
volundr helm values <chart>        # Generate values.yaml

volundr kustomize init <name>      # Initialize Kustomize base
volundr kustomize overlay <base>   # Generate overlay

volundr argocd app <repo>          # Generate ArgoCD Application
volundr flux source <repo>         # Generate Flux GitRepository

volundr validate kubernetes <dir>  # Validate K8s manifests
volundr validate terraform <dir>   # Validate Terraform

volundr scaffold microservice <name>  # Full microservice scaffold
volundr scaffold monorepo <name>      # Monorepo structure
```

Add common flags:
```
--format text|json|yaml            Output format
--output <dir>                     Output directory
--template <name>                  Template to use
--dry-run                          Preview without writing
```

### 5.3 Validation Integration

- Kubernetes manifest validation (kubeconform integration)
- Terraform plan validation
- Dockerfile best practices (hadolint integration)
- Security scanning (trivy integration)

### 5.4 Template System

- Custom template support
- Template inheritance
- Variable substitution
- Conditional sections

---

## Phase 6: Testing and Documentation

### 6.1 Test Coverage

Each module should have:
- **L0 Unit Tests**: 90%+ coverage on services
- **L1 Functional Tests**: CLI command testing
- **L2 Integration Tests**: Cross-service testing
- **L3 Contract Tests**: API/model validation

### 6.2 Documentation

Each module should have:
- README.md with quick start and examples
- CLI help text for all commands
- Pydantic model documentation
- Integration guides

### 6.3 Self-Testing

- Freya should visually test its own reports
- Forseti should validate its own schemas
- Verdandi should measure its own performance
- Volundr should generate its own deployment configs

---

## Implementation Priority

### Sprint 1: Common Infrastructure
1. Extract parallel/incremental/baseline to common module
2. Extend AsgardConfig for all modules
3. Create UnifiedFormatter
4. Update all CLIs with common flags

### Sprint 2: Freya Expansion
1. PerformanceScanner and SEOScanner
2. SecurityHeaderScanner
3. Parallel URL processing
4. Enhanced HTML reporting

### Sprint 3: Forseti Expansion
1. MockServerGenerator
2. SDKGenerator (TypeScript, Python)
3. Breaking change impact analysis
4. CI/CD integration

### Sprint 4: Verdandi Expansion
1. APMAnalyzer and TracingAnalyzer
2. SLO/Error Budget calculator
3. RegressionDetector
4. Data source integrations

### Sprint 5: Volundr Expansion
1. HelmChartGenerator
2. KustomizeGenerator
3. GitOps generators (ArgoCD, Flux)
4. Validation integrations

### Sprint 6: Testing and Polish
1. L0-L3 tests for all new features
2. Documentation updates
3. Self-testing implementation
4. Performance optimization

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Module file count | All modules >= 80 files |
| CLI commands per module | >= 15 commands |
| Test coverage | >= 90% for all services |
| Documentation completeness | README + CLI help for all commands |
| Self-lint passing | Heimdall quality checks pass on all modules |

---

## Dependencies

- Playwright (Freya performance/console testing)
- Jinja2 (template generation)
- PyYAML (config/manifest handling)
- OpenTelemetry SDK (Verdandi tracing)
- kubernetes-client (Volundr validation)
- requests/httpx (API testing)

---

## Notes

- Each enhancement should follow Heimdall's pattern:
  1. Pydantic models in `models/`
  2. Service classes in `services/`
  3. CLI integration in `cli.py`
  4. Tests in `Asgard_Test/`
- All new code should use type annotations
- All CLI commands should support `--format text|json|github`
- All scanners should support parallel and incremental modes where applicable
