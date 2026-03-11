"""
Heimdall SBOM Generator

Generates Software Bill of Materials (SBOM) documents in SPDX 2.3 and
CycloneDX 1.4 formats by scanning dependency declaration files.
"""

import importlib.metadata
import re
import tomllib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from Asgard.Heimdall.Dependencies.models.sbom_models import (
    ComponentType,
    SBOMComponent,
    SBOMConfig,
    SBOMDocument,
    SBOMFormat,
)


class SBOMGenerator:
    """
    Generates SBOM documents from project dependency files.

    Scans for requirements.txt, pyproject.toml, and other common Python
    dependency declaration files, then produces a structured SBOM document
    in either SPDX 2.3 or CycloneDX 1.4 JSON format.
    """

    def __init__(self, config: Optional[SBOMConfig] = None) -> None:
        self._config = config or SBOMConfig()

    def generate(self, scan_path: Optional[str] = None) -> SBOMDocument:
        """
        Generate an SBOM document by scanning the given path for dependency files.

        Args:
            scan_path: Directory to scan. Overrides config.scan_path when provided.

        Returns:
            A populated SBOMDocument instance.
        """
        resolved_path = Path(scan_path).resolve() if scan_path else Path(self._config.scan_path).resolve()
        project_name = self._config.project_name or resolved_path.name

        components: List[SBOMComponent] = []
        seen: set = set()

        for filename in self._config.requirements_files:
            candidate = resolved_path / filename
            if not candidate.exists():
                continue

            if filename in ("requirements.txt", "requirements-dev.txt"):
                pairs = self._parse_requirements_txt(str(candidate))
            elif filename == "pyproject.toml":
                pairs = self._parse_pyproject_toml(str(candidate))
            else:
                pairs = self._parse_requirements_txt(str(candidate))

            for name, version in pairs:
                key = (name.lower(), version)
                if key in seen:
                    continue
                seen.add(key)

                license_id = self._get_license_from_metadata(name)
                purl = self._make_purl(name, version)

                component = SBOMComponent(
                    name=name,
                    version=version,
                    component_type=ComponentType.LIBRARY,
                    license_id=license_id,
                    purl=purl,
                    is_transitive=False,
                )
                components.append(component)

        fmt = SBOMFormat(self._config.output_format) if isinstance(self._config.output_format, str) else self._config.output_format
        spec_version = "2.3" if fmt == SBOMFormat.SPDX else "1.4"
        document_id = str(uuid.uuid4())
        now = datetime.now()

        document = SBOMDocument(
            format=fmt,
            spec_version=spec_version,
            document_id=document_id,
            document_name=f"SBOM-{project_name}",
            project_name=project_name,
            project_version=self._config.project_version,
            created_at=now,
            components=components,
            total_components=len(components),
            direct_dependencies=len(components),
            transitive_dependencies=0,
        )
        return document

    def to_spdx_json(self, document: SBOMDocument) -> Dict[str, Any]:
        """
        Convert an SBOMDocument to a valid SPDX 2.3 JSON representation.

        Args:
            document: The SBOM document to convert.

        Returns:
            Dictionary conforming to the SPDX 2.3 JSON schema.
        """
        packages = []
        for component in document.components:
            name = component.name if isinstance(component, SBOMComponent) else component["name"]
            version = component.version if isinstance(component, SBOMComponent) else component["version"]
            license_id = component.license_id if isinstance(component, SBOMComponent) else component.get("license_id", "")
            purl = component.purl if isinstance(component, SBOMComponent) else component.get("purl", "")

            spdx_id = f"SPDXRef-Package-{re.sub(r'[^a-zA-Z0-9.-]', '-', name)}"
            concluded_license = license_id if license_id else "NOASSERTION"

            package: Dict[str, Any] = {
                "SPDXID": spdx_id,
                "name": name,
                "versionInfo": version,
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": concluded_license,
                "licenseDeclared": concluded_license,
                "copyrightText": "NOASSERTION",
            }
            if purl:
                package["externalRefs"] = [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": purl,
                    }
                ]
            packages.append(package)

        doc_id = document.document_id if isinstance(document.document_id, str) else str(document.document_id)
        created_at = document.created_at if isinstance(document.created_at, datetime) else datetime.fromisoformat(str(document.created_at))
        project_name = document.project_name if isinstance(document.project_name, str) else str(document.project_name)
        document_name = document.document_name if isinstance(document.document_name, str) else str(document.document_name)
        creator_tool = document.creator_tool if isinstance(document.creator_tool, str) else str(document.creator_tool)

        result: Dict[str, Any] = {
            "SPDXID": "SPDXRef-DOCUMENT",
            "spdxVersion": "SPDX-2.3",
            "creationInfo": {
                "created": created_at.isoformat() + "Z",
                "creators": [
                    f"Tool: {creator_tool}",
                ],
            },
            "name": document_name,
            "dataLicense": "CC0-1.0",
            "documentNamespace": f"https://spdx.org/spdxdocs/{project_name}-{doc_id}",
            "packages": packages,
        }
        return result

    def to_cyclonedx_json(self, document: SBOMDocument) -> Dict[str, Any]:
        """
        Convert an SBOMDocument to a valid CycloneDX 1.4 JSON representation.

        Args:
            document: The SBOM document to convert.

        Returns:
            Dictionary conforming to the CycloneDX 1.4 JSON schema.
        """
        components = []
        for component in document.components:
            name = component.name if isinstance(component, SBOMComponent) else component["name"]
            version = component.version if isinstance(component, SBOMComponent) else component["version"]
            purl = component.purl if isinstance(component, SBOMComponent) else component.get("purl", "")
            license_id = component.license_id if isinstance(component, SBOMComponent) else component.get("license_id", "")
            comp_type = "library"

            cdx_component: Dict[str, Any] = {
                "type": comp_type,
                "name": name,
                "version": version,
            }
            if purl:
                cdx_component["purl"] = purl
            if license_id:
                cdx_component["licenses"] = [{"license": {"id": license_id}}]
            components.append(cdx_component)

        doc_id = document.document_id if isinstance(document.document_id, str) else str(document.document_id)
        created_at = document.created_at if isinstance(document.created_at, datetime) else datetime.fromisoformat(str(document.created_at))
        creator_tool = document.creator_tool if isinstance(document.creator_tool, str) else str(document.creator_tool)

        result: Dict[str, Any] = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "serialNumber": f"urn:uuid:{doc_id}",
            "version": 1,
            "metadata": {
                "timestamp": created_at.isoformat() + "Z",
                "tools": [
                    {
                        "name": creator_tool,
                    }
                ],
            },
            "components": components,
        }
        return result

    def _parse_requirements_txt(self, file_path: str) -> List[Tuple[str, str]]:
        """
        Parse a requirements.txt file and return (name, version_spec) pairs.

        Handles standard pin syntax (==, >=, <=, ~=, !=, >).
        Skips comments, blank lines, -r includes, and -e editable installs.

        Args:
            file_path: Absolute path to the requirements file.

        Returns:
            List of (package_name, version_spec) tuples.
        """
        results: List[Tuple[str, str]] = []

        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                for raw_line in fh:
                    line = raw_line.strip()
                    if not line:
                        continue
                    if line.startswith("#"):
                        continue
                    if line.startswith("-r ") or line.startswith("--requirement"):
                        continue
                    if line.startswith("-e ") or line.startswith("--editable"):
                        continue
                    if line.startswith("-"):
                        continue

                    # Strip inline comments
                    line = line.split(" #")[0].strip()
                    line = line.split("\t#")[0].strip()

                    # Match package name with optional version constraint
                    match = re.match(
                        r"^([A-Za-z0-9_\-\.]+)\s*([><=!~][><=!~]?\s*[^\s;,]+)?",
                        line,
                    )
                    if match:
                        name = match.group(1).strip()
                        version_spec = match.group(2).strip() if match.group(2) else ""
                        results.append((name, version_spec))
        except (OSError, IOError):
            pass

        return results

    def _parse_pyproject_toml(self, file_path: str) -> List[Tuple[str, str]]:
        """
        Parse a pyproject.toml file and return (name, version_spec) pairs.

        Reads from [project.dependencies] (PEP 621) and
        [tool.poetry.dependencies] (Poetry). Returns empty list on parse failure.

        Args:
            file_path: Absolute path to pyproject.toml.

        Returns:
            List of (package_name, version_spec) tuples.
        """
        results: List[Tuple[str, str]] = []

        try:
            with open(file_path, "rb") as fh:
                data = tomllib.load(fh)
        except Exception:
            return results

        # PEP 621: [project.dependencies]
        project_deps = data.get("project", {}).get("dependencies", [])
        for dep in project_deps:
            if not isinstance(dep, str):
                continue
            match = re.match(
                r"^([A-Za-z0-9_\-\.]+)\s*([><=!~][><=!~]?\s*[^\s;,]+)?",
                dep.strip(),
            )
            if match:
                name = match.group(1).strip()
                version_spec = match.group(2).strip() if match.group(2) else ""
                results.append((name, version_spec))

        # Poetry: [tool.poetry.dependencies]
        poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        for name, spec in poetry_deps.items():
            if name.lower() == "python":
                continue
            if isinstance(spec, str):
                version_spec = spec
            elif isinstance(spec, dict):
                version_spec = spec.get("version", "")
            else:
                version_spec = ""
            results.append((name, version_spec))

        return results

    def _make_purl(self, name: str, version: str, ecosystem: str = "pypi") -> str:
        """
        Build a Package URL (purl) for the given package.

        Args:
            name: Package name.
            version: Version string or version spec.
            ecosystem: Package ecosystem identifier (default: pypi).

        Returns:
            A purl string such as "pkg:pypi/requests@2.28.0".
        """
        normalized = name.lower().replace("-", "_")
        if version:
            # Strip leading operator characters to get the raw version for purl
            clean_version = re.sub(r"^[><=!~]+\s*", "", version).strip()
            return f"pkg:{ecosystem}/{normalized}@{clean_version}"
        return f"pkg:{ecosystem}/{normalized}"

    def _get_license_from_metadata(self, package_name: str) -> str:
        """
        Retrieve the license identifier for an installed package using importlib.metadata.

        Args:
            package_name: The package name to look up.

        Returns:
            SPDX license identifier string, or empty string if not available.
        """
        try:
            meta = importlib.metadata.metadata(package_name)
            license_value = meta.get("License", "")
            if license_value:
                return license_value.strip()
        except importlib.metadata.PackageNotFoundError:
            pass
        except Exception:
            pass
        return ""
