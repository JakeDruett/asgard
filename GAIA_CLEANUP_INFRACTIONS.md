# Asgard GAIA Cleanup Infractions Report

> **Purpose**: This document catalogs every reference to GAIA, sibling projects (Triton/Lexicon), developer-specific data, and structural leaks that must be removed to make Asgard a 100% standalone, universal package.
>
> **Generated**: 2026-02-13
>
> **Total Infractions**: 100+ across 78+ files

---

## Table of Contents

1. [CRITICAL: Entire Directory to Remove](#1-critical-entire-directory-to-remove)
2. [CRITICAL: Project Metadata Files](#2-critical-project-metadata-files)
3. [CRITICAL: Sibling Project References (Triton/Lexicon)](#3-critical-sibling-project-references-tritonlexicon)
4. [HIGH: Module Docstrings and Author Attributions](#4-high-module-docstrings-and-author-attributions)
5. [HIGH: CLI Descriptions](#5-high-cli-descriptions)
6. [HIGH: README Documentation](#6-high-readme-documentation)
7. [HIGH: GAIA Coding Standards References](#7-high-gaia-coding-standards-references)
8. [HIGH: GAIA-Style Architecture References](#8-high-gaia-style-architecture-references)
9. [MEDIUM: HTML Report Output and User-Agent Strings](#9-medium-html-report-output-and-user-agent-strings)
10. [MEDIUM: Default Theme Name](#10-medium-default-theme-name)
11. [MEDIUM: Hardcoded Developer Filesystem Paths](#11-medium-hardcoded-developer-filesystem-paths)
12. [MEDIUM: Git Commit History](#12-medium-git-commit-history)
13. [LOW: Test Files with GAIA References](#13-low-test-files-with-gaia-references)
14. [Tracked Coverage File](#14-tracked-coverage-file)

---

## 1. CRITICAL: Entire Directory to Remove

### `_GAIA Documentation/` directory

**Action**: DELETE the entire directory and all contents.

| File | Action |
|------|--------|
| `_GAIA Documentation/Asgard-Module-Expansion-Plan.md` | DELETE |

This is a 15KB internal GAIA planning document that reveals the full expansion roadmap, GAIA's relationship to Asgard, and internal development strategy. It must be completely removed from the repository and git history.

---

## 2. CRITICAL: Project Metadata Files

### `pyproject.toml`

| Line | Current Content | Required Change |
|------|----------------|-----------------|
| 8 | `description = "Asgard - GAIA Development Tools Suite"` | Change to `description = "Asgard - Universal Development Tools Suite"` |
| 13 | `{name = "GAIA Team", email = "team@gaia.ai"}` | Change to generic author info (e.g., `{name = "Asgard Contributors", email = "asgard@example.com"}`) or the actual open-source maintainer |
| 88 | `Homepage = "https://github.com/gaia/asgard"` | Update to actual public repo URL |
| 89 | `Documentation = "https://github.com/gaia/asgard#readme"` | Update to actual public repo URL |
| 90 | `Repository = "https://github.com/gaia/asgard"` | Update to actual public repo URL |

### `setup.py`

| Line | Current Content | Required Change |
|------|----------------|-----------------|
| 12 | `description="Asgard - GAIA Development Tools Suite",` | Change to `"Asgard - Universal Development Tools Suite"` |
| 14 | `Asgard is GAIA's comprehensive suite of development and quality assurance tools,` | Rewrite to remove GAIA ownership claim |
| 17 | `GAIA's codebase.` | Remove GAIA reference |
| 91 | `author="GAIA Team",` | Change to `"Asgard Contributors"` or actual maintainer |
| 92 | `author_email="team@gaia.ai",` | Update email |
| 93 | `url="https://github.com/gaia/asgard",` | Update to actual repo URL |

> **Note**: `setup.py` should ideally be removed entirely (see improvement report) since `pyproject.toml` is the modern standard. If kept, all GAIA references must be cleaned.

---

## 3. CRITICAL: Sibling Project References (Triton/Lexicon)

These are references to GAIA's internal wrapper libraries **Triton** (message broker/cache) and **Lexicon** (database/vault). These MUST be replaced with generic, configurable defaults for a standalone tool.

### `Asgard/config/defaults.py`

| Lines | Current Content | Required Change |
|-------|----------------|-----------------|
| 37 | `# Default forbidden imports for GAIA projects` | Change to `# Default forbidden imports (configurable)` |
| 38-47 | Entire `DEFAULT_FORBIDDEN_IMPORTS` dict references Triton and Lexicon | Replace with an empty dict `{}` or generic examples, making it purely user-configurable |
| 71-74 | `DEFAULT_ALLOWED_PATHS` references `**/Triton/**` and `**/Lexicon/**` | Replace with `["**/wrappers/**"]` or empty list |

### `Asgard/config/models.py`

| Lines | Current Content | Required Change |
|-------|----------------|-----------------|
| 92-101 | `ForbiddenImportConfig.forbidden_modules` default references Triton/Lexicon | Change default to empty dict `{}` |
| 104-108 | `ForbiddenImportConfig.allowed_paths` default references Triton/Lexicon | Change default to `["**/wrappers/**"]` or empty list |

### `Asgard/Heimdall/Quality/models/library_usage_models.py`

| Lines | Current Content | Required Change |
|-------|----------------|-----------------|
| 101-110 | `ForbiddenImportConfig.forbidden_modules` default references Triton/Lexicon | Change default to empty dict `{}` |
| 113-118 | `ForbiddenImportConfig.allowed_paths` default references Triton/Lexicon | Change default to `["**/wrappers/**"]` or empty list |

### `Asgard/Heimdall/Quality/services/library_usage_scanner.py`

| Line | Current Content | Required Change |
|------|----------------|-----------------|
| 129 | Docstring mentions `pika -> Triton, redis -> Triton` | Replace with generic description of the forbidden imports feature |

---

## 4. HIGH: Module Docstrings and Author Attributions

Every module's `__init__.py` contains `__author__ = "GAIA Team"` and docstrings claiming GAIA ownership. All must be updated.

### Main Package

| File | Lines | Current | Fix |
|------|-------|---------|-----|
| `Asgard/__init__.py` | 2 | `Asgard - GAIA Development Tools Suite` | `Asgard - Universal Development Tools Suite` |
| `Asgard/__init__.py` | 4-7 | `Asgard is GAIA's comprehensive...watch over and forge GAIA's codebase.` | Remove all GAIA ownership language |
| `Asgard/__init__.py` | 18 | `__author__ = "GAIA Team"` | `__author__ = "Asgard Contributors"` |
| `Asgard/__init__.py` | 24 | `"description": "GAIA Development Tools Suite"` | `"description": "Universal Development Tools Suite"` |

### Heimdall Module

| File | Lines | Fix |
|------|-------|-----|
| `Asgard/Heimdall/__init__.py` | 2 | Change `GAIA Code Quality Control` → `Code Quality Control` |
| `Asgard/Heimdall/__init__.py` | 74 | Change `__author__` from `"GAIA Team"` |
| `Asgard/Heimdall/__init__.py` | 80 | Change `"Code quality control package for GAIA"` |
| `Asgard/Heimdall/Quality/__init__.py` | 78 | Change `__author__` |
| `Asgard/Heimdall/OOP/__init__.py` | 38 | Change `__author__` |
| `Asgard/Heimdall/Performance/__init__.py` | 26 | Change `__author__` |
| `Asgard/Heimdall/Security/__init__.py` | 38 | Change `__author__` |
| `Asgard/Heimdall/Security/Auth/__init__.py` | 22 | Change `__author__` |
| `Asgard/Heimdall/Security/Headers/__init__.py` | 23 | Change `__author__` |
| `Asgard/Heimdall/Security/TLS/__init__.py` | 22 | Change `__author__` |
| `Asgard/Heimdall/Security/Container/__init__.py` | 23 | Change `__author__` |
| `Asgard/Heimdall/Security/Infrastructure/__init__.py` | 22 | Change `__author__` |
| `Asgard/Heimdall/Security/Access/__init__.py` | 22 | Change `__author__` |
| `Asgard/Heimdall/Dependencies/__init__.py` | 35 | Change `__author__` |

### Freya Module

| File | Lines | Fix |
|------|-------|-----|
| `Asgard/Freya/__init__.py` | 2 | Change `Visual and UI Testing Package for GAIA` |
| `Asgard/Freya/__init__.py` | 36 | Change `__author__` |
| `Asgard/Freya/__init__.py` | 41 | Change `"Visual and UI testing package for GAIA"` |

### Forseti Module

| File | Lines | Fix |
|------|-------|-----|
| `Asgard/Forseti/__init__.py` | 2 | Change `GAIA API and Schema Specification Library` |
| `Asgard/Forseti/__init__.py` | 63 | Change `__author__` |
| `Asgard/Forseti/__init__.py` | 69 | Change `"API and schema specification library for GAIA"` |
| `Asgard/Forseti/Database/__init__.py` | 19 | Change `__author__` |
| `Asgard/Forseti/OpenAPI/__init__.py` | 29 | Change `__author__` |
| `Asgard/Forseti/GraphQL/__init__.py` | 21 | Change `__author__` |
| `Asgard/Forseti/Avro/__init__.py` | 28 | Change `__author__` |
| `Asgard/Forseti/AsyncAPI/__init__.py` | 29 | Change `__author__` |
| `Asgard/Forseti/Protobuf/__init__.py` | 28 | Change `__author__` |
| `Asgard/Forseti/Contracts/__init__.py` | 19 | Change `__author__` |
| `Asgard/Forseti/Documentation/__init__.py` | 27 | Change `__author__` |
| `Asgard/Forseti/MockServer/__init__.py` | 29 | Change `__author__` |
| `Asgard/Forseti/CodeGen/__init__.py` | 33 | Change `__author__` |

### Verdandi Module

| File | Lines | Fix |
|------|-------|-----|
| `Asgard/Verdandi/__init__.py` | 2 | Change `GAIA Runtime Performance Metrics` |
| `Asgard/Verdandi/__init__.py` | 49 | Change `__author__` |
| `Asgard/Verdandi/__init__.py` | 54 | Change `"Runtime performance metrics package for GAIA"` |
| `Asgard/Verdandi/Trend/__init__.py` | 21 | Change `__author__` |
| `Asgard/Verdandi/Analysis/__init__.py` | 26 | Change `__author__` |
| `Asgard/Verdandi/Cache/__init__.py` | 19 | Change `__author__` |
| `Asgard/Verdandi/Web/__init__.py` | 19 | Change `__author__` |
| `Asgard/Verdandi/System/__init__.py` | 19 | Change `__author__` |
| `Asgard/Verdandi/Network/__init__.py` | 19 | Change `__author__` |
| `Asgard/Verdandi/APM/__init__.py` | 26 | Change `__author__` |
| `Asgard/Verdandi/Tracing/__init__.py` | 21 | Change `__author__` |
| `Asgard/Verdandi/Anomaly/__init__.py` | 26 | Change `__author__` |
| `Asgard/Verdandi/SLO/__init__.py` | 27 | Change `__author__` |
| `Asgard/Verdandi/Database/__init__.py` | 19 | Change `__author__` |

### Volundr Module

| File | Lines | Fix |
|------|-------|-----|
| `Asgard/Volundr/__init__.py` | 2 | Change `GAIA Infrastructure Generation Library` |
| `Asgard/Volundr/__init__.py` | 56 | Change `__author__` |
| `Asgard/Volundr/__init__.py` | 61 | Change `"Infrastructure generation library for GAIA"` |

### Universal Fix

For **ALL** `__init__.py` files listed above:
- Replace `__author__ = "GAIA Team"` with `__author__ = "Asgard Contributors"`
- Replace any `"... for GAIA"` description with `"..."` (remove "for GAIA")
- Replace `"GAIA ..."` prefixes with `"Asgard ..."` or just the module name

---

## 5. HIGH: CLI Descriptions

| File | Line | Current Content | Fix |
|------|------|----------------|-----|
| `Asgard/cli.py` | 2 | `Unified command-line interface for GAIA development tools.` | Remove `GAIA` |
| `Asgard/cli.py` | 58 | `ASGARD - GAIA Development Tools Suite` | `ASGARD - Universal Development Tools Suite` |
| `Asgard/cli.py` | 337 | `description="Asgard - GAIA Development Tools Suite"` | Remove `GAIA` |
| `Asgard/Heimdall/cli/main.py` | 65 | `description="Heimdall - Code Quality Control for GAIA"` | Remove `for GAIA` |
| `Asgard/Freya/cli.py` | 111 | `description="Freya - Visual and UI Testing for GAIA"` | Remove `for GAIA` |
| `Asgard/Verdandi/cli.py` | 48 | `description="Verdandi - Runtime Performance Metrics for GAIA"` | Remove `for GAIA` |
| `Asgard/Volundr/cli.py` | 113 | `description="Volundr - Infrastructure Generation for GAIA"` | Remove `for GAIA` |

---

## 6. HIGH: README Documentation

### `README.md` (Root)

| Line | Current Content | Fix |
|------|----------------|-----|
| 3 | `Named after the realm of the Norse gods, Asgard is GAIA's comprehensive suite of development and quality assurance tools. Like the mythical realm that houses the great halls of the Aesir, Asgard houses the tools that watch over and forge a codebase.` | Remove `GAIA's` - rewrite as standalone project description |

### Module READMEs

| File | Line | Fix |
|------|------|-----|
| `Asgard/Heimdall/README.md` | 7 | Remove `GAIA's` ownership claim in description |
| `Asgard/Heimdall/README.md` | 303 | Change `GAIA Team` author attribution |
| `Asgard/Freya/README.md` | 7 | Remove `GAIA's` ownership claim in description |
| `Asgard/Freya/README.md` | 323 | Change `GAIA Team` author attribution |
| `Asgard/Forseti/README.md` | 7 | Remove `GAIA's` ownership claim in description |
| `Asgard/Forseti/README.md` | 355 | Change `GAIA Team` author attribution |
| `Asgard/Verdandi/README.md` | 7 | Remove `GAIA's` ownership claim in description |
| `Asgard/Verdandi/README.md` | 434 | Change `GAIA Team` author attribution |
| `Asgard/Volundr/README.md` | 7 | Remove `GAIA's` ownership claim in description |
| `Asgard/Volundr/README.md` | 535 | Change `GAIA Team` author attribution |
| `Asgard/Volundr/COMPATIBILITY.md` | 510 | Change `**Owner**: GAIA Infrastructure Team` |

---

## 7. HIGH: GAIA Coding Standards References

These files reference "GAIA coding standard" as though it's the governing standard. For a universal tool, these should reference configurable best practices, not GAIA-specific standards.

| File | Line(s) | Current Content | Fix |
|------|---------|----------------|-----|
| `Asgard/Heimdall/Quality/models/env_fallback_models.py` | 5 | `access which violates the GAIA coding standard that prohibits fallback values` | Change to `which violates the configured coding standard that prohibits fallback values` |
| `Asgard/Heimdall/Quality/models/lazy_import_models.py` | 5 | `violate the GAIA coding standard` | Change to `violate the configured coding standard` |
| `Asgard/Heimdall/Quality/services/env_fallback_scanner.py` | 5, 380 | `violates the GAIA coding standard` | Change to `violates the configured coding standard` |
| `Asgard/Heimdall/Quality/services/lazy_import_scanner.py` | 5, 249 | `the GAIA coding standard that ALL imports MUST be at the top of the file` | Change to `the coding standard that ALL imports MUST be at the top of the file` |

---

## 8. HIGH: GAIA-Style Architecture References

| File | Line | Current Content | Fix |
|------|------|----------------|-----|
| `Asgard/Heimdall/Architecture/services/layer_analyzer.py` | 31 | `# Default GAIA-style layer definitions` | `# Default layer definitions` |
| `Asgard/Heimdall/Dependencies/services/modularity_analyzer.py` | 276 | `# Default GAIA-style layers` | `# Default layers` |

---

## 9. MEDIUM: HTML Report Output and User-Agent Strings

### HTML Report Footers

| File | Line | Current Content | Fix |
|------|------|----------------|-----|
| `Asgard/Freya/Integration/services/site_crawler.py` | 1259 | `<p>Generated by Freya - Visual and UI Testing for GAIA</p>` | `<p>Generated by Freya - Visual and UI Testing</p>` |
| `Asgard/Freya/Integration/services/html_reporter.py` | 190 | `<p>Generated by Freya - GAIA Visual Testing Framework</p>` | `<p>Generated by Freya - Visual Testing Framework</p>` |

### User-Agent Strings (references `gaia-assistant.com`)

| File | Line | Current Content | Fix |
|------|------|----------------|-----|
| `Asgard/Freya/Images/services/image_optimization_scanner.py` | 59-60 | `"Mozilla/5.0 (compatible; FreyaBot/1.0; +https://gaia-assistant.com/bots)"` | Change URL to a generic or Asgard-specific URL |
| `Asgard/Freya/Links/services/link_validator.py` | 55-56 | `"Mozilla/5.0 (compatible; FreyaBot/1.0; +https://gaia-assistant.com/bots)"` | Change URL |
| `Asgard/Freya/SEO/services/robots_analyzer.py` | 48-49 | `"Mozilla/5.0 (compatible; FreyaBot/1.0; +https://gaia-assistant.com/bots)"` | Change URL |

---

## 10. MEDIUM: Default Theme Name

| File | Line | Current Content | Fix |
|------|------|----------------|-----|
| `Asgard/Freya/Integration/models/integration_models.py` | 158 | `theme: str = Field(default="gaia", description="Report theme")` | Change default to `"default"` or `"asgard"` |

---

## 11. MEDIUM: Hardcoded Developer Filesystem Paths

Multiple test documentation files contain the developer's local filesystem path `/mnt/storage/home-data/Documents/GAIA`. These reveal the developer's machine structure and the GAIA parent project.

| File | Line(s) | Content |
|------|---------|---------|
| `Asgard_Test/L2_CrossPackage/QUICK_START.md` | 6, 98, 116 | `cd /mnt/storage/home-data/Documents/GAIA` |
| `Asgard_Test/L2_CrossPackage/TEST_SUMMARY.md` | 179, 182 | `cd /mnt/storage/home-data/Documents/GAIA` |
| `Asgard_Test/L2_CrossPackage/README.md` | 79 | `cd /mnt/storage/home-data/Documents/GAIA/Asgard/Asgard_Test` |
| `Asgard_Test/L0_unit/forseti/TEST_SUMMARY.md` | 190 | `/mnt/storage/home-data/Documents/GAIA/Asgard/Asgard_Test/L0_unit/forseti/` |
| `Asgard_Test/test_utils/SUMMARY.md` | 6, 200 | `/mnt/storage/home-data/Documents/GAIA/Asgard/Asgard_Test/test_utils/` |
| `Asgard_Test/tests_Forseti/L1_Integration/TEST_SUMMARY.md` | 282 | `/mnt/storage/home-data/Documents/GAIA/Asgard/Asgard_Test/tests_Forseti/L1_Integration/` |
| `Asgard_Test/tests_Freya/L1_Integration/README.md` | 181 | `export PYTHONPATH=/mnt/storage/home-data/Documents/GAIA:$PYTHONPATH` |
| `Asgard_Test/tests_Heimdall/SECURITY_COVERAGE_AUDIT.md` | 6 | `/mnt/storage/home-data/Documents/GAIA/Asgard/Asgard_Test/tests_Heimdall/L0_Mocked/Security/` |
| `Asgard_Test/tests_Verdandi/L0_Mocked/TEST_STATISTICAL_VALIDATION_README.md` | 201 | `cd /mnt/storage/home-data/Documents/GAIA` |

**Fix**: Replace all instances of `/mnt/storage/home-data/Documents/GAIA` with relative paths (e.g., `./` or `<project-root>/`). Use `cd Asgard_Test/` instead of absolute paths.

---

## 12. MEDIUM: Git Commit History

| Commit | Message |
|--------|---------|
| `cfb826d` | `Initial release of Asgard - GAIA Development Tools Suite` |

**Fix**: Consider rewriting git history if publishing as open source, or accept that the initial commit message contains this reference. At minimum, future commits should not reference GAIA.

---

## 13. LOW: Test Files with GAIA References

### Test Configuration and Assertions

| File | Line | Content | Fix |
|------|------|---------|-----|
| `Asgard_Test/tests_Freya/L0_Mocked/Integration/test_integration_models.py` | 343 | `assert config.theme == "gaia"` | Update assertion after theme default changes to `"default"` or `"asgard"` |
| `Asgard_Test/tests_Freya/L0_Mocked/Integration/test_html_reporter.py` | 32 | `theme="gaia",` | Update test fixture |

### Test Documentation

| File | Line | Content | Fix |
|------|------|---------|-----|
| `Asgard_Test/README.md` | 26, 30 | `# From GAIA root directory` / `# Or from GAIA root` | Change to `# From Asgard root directory` |
| `Asgard_Test/L0_unit/verdandi/README.md` | 250 | `Part of the GAIA Asgard project.` | Change to `Part of the Asgard project.` |

---

## 14. Tracked Coverage File

| File | Size | Issue |
|------|------|-------|
| `.coverage` | 53KB | This binary file is tracked in git despite being in `.gitignore`. It was likely committed before the gitignore rule was added. |

**Fix**: Run `git rm --cached .coverage` and commit the removal.

---

## Summary of Changes Required

| Priority | Category | Files Affected | Action |
|----------|----------|---------------|--------|
| CRITICAL | `_GAIA Documentation/` directory | 1 | DELETE entirely |
| CRITICAL | `pyproject.toml` | 1 | 5 line changes |
| CRITICAL | `setup.py` | 1 | 6 line changes (or DELETE file) |
| CRITICAL | Triton/Lexicon references | 4 | Replace defaults with empty/generic |
| HIGH | `__init__.py` author/docstrings | ~40 | `s/GAIA Team/Asgard Contributors/` and remove GAIA descriptions |
| HIGH | CLI descriptions | 5 | Remove "for GAIA" |
| HIGH | README files | 6 | Rewrite GAIA ownership claims |
| HIGH | Coding standards references | 4 | Remove "GAIA" qualifier |
| HIGH | Architecture references | 2 | Remove "GAIA-style" prefix |
| MEDIUM | HTML output / User-Agents | 5 | Remove GAIA URLs and branding |
| MEDIUM | Theme default | 1 | `"gaia"` → `"default"` |
| MEDIUM | Hardcoded paths | 9 | Replace absolute paths with relative |
| MEDIUM | Git history | N/A | Optional rewrite |
| LOW | Test files | 4 | Update assertions and docs |
| LOW | `.coverage` file | 1 | `git rm --cached` |

### Quick Grep Validation Commands

After cleanup, run these commands to verify zero GAIA references remain:

```bash
# Should return ZERO results (excluding this report file itself)
grep -ri "gaia" --include="*.py" --include="*.md" --include="*.toml" --include="*.cfg" --include="*.ini" --include="*.yaml" --include="*.yml" .

# Check for Triton/Lexicon sibling projects
grep -ri "triton\|lexicon" --include="*.py" .

# Check for hardcoded developer paths
grep -r "/mnt/storage/home-data" .

# Check for gaia-assistant.com
grep -r "gaia-assistant" .

# Check for team@gaia.ai
grep -r "team@gaia" .
```
