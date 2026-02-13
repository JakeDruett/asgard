"""
Setup file for Asgard package.
This installs Asgard and all its subpackages (Heimdall, Freya, Forseti, Verdandi, Volundr)
as a unified Python package.
"""

from setuptools import setup, find_packages

setup(
    name="Asgard",
    version="1.0.0",
    description="Asgard - GAIA Development Tools Suite",
    long_description="""
    Asgard is GAIA's comprehensive suite of development and quality assurance tools,
    named after the realm of the Norse gods. Like the mythical realm that houses
    the great halls of the Aesir, Asgard houses the tools that watch over and forge
    GAIA's codebase.

    Subpackages:
    - Heimdall: Code quality control and static analysis (the watchman)
    - Freya: Visual and UI testing (the goddess of beauty)
    - Forseti: API and schema specification (the god of justice/contracts)
    - Verdandi: Runtime performance metrics (the Norn of the present)
    - Volundr: Infrastructure generation (the master smith)
    """,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["Asgard_Test", "Asgard_Test.*"]),
    install_requires=[
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "jsonschema>=4.0",
        "playwright>=1.40.0",
        "Pillow>=10.0.0",
        "beautifulsoup4>=4.12.0",
    ],
    extras_require={
        "heimdall": [
            "bandit>=1.7.0",
            "memory-profiler>=0.60.0",
        ],
        "freya": [
            "numpy>=1.24.0",
            "scikit-image>=0.21.0",
            "opencv-python>=4.8.0",
            "cssutils>=2.7.0",
            "Jinja2>=3.1.0",
        ],
        "forseti": [
            "openapi-spec-validator>=0.5.0",
            "openapi-schema-validator>=0.6.0",
            "graphql-core>=3.2.0",
            "sqlalchemy>=2.0",
        ],
        "volundr": [
            "python-hcl2>=4.0.0",
        ],
        "all": [
            "bandit>=1.7.0",
            "memory-profiler>=0.60.0",
            "numpy>=1.24.0",
            "scikit-image>=0.21.0",
            "opencv-python>=4.8.0",
            "cssutils>=2.7.0",
            "Jinja2>=3.1.0",
            "openapi-spec-validator>=0.5.0",
            "openapi-schema-validator>=0.6.0",
            "graphql-core>=3.2.0",
            "sqlalchemy>=2.0",
            "python-hcl2>=4.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # Unified CLI
            "asgard=Asgard.cli:main",
            # Individual module CLIs (backwards compatible)
            "heimdall=Asgard.Heimdall.cli:main",
            "freya=Asgard.Freya.cli:main",
            "forseti=Asgard.Forseti.cli:main",
            "verdandi=Asgard.Verdandi.cli:main",
            "volundr=Asgard.Volundr.cli:main",
        ],
    },
    python_requires=">=3.11",
    author="GAIA Team",
    author_email="team@gaia.ai",
    url="https://github.com/gaia/asgard",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Build Tools",
    ],
    include_package_data=True,
    zip_safe=False,
)
