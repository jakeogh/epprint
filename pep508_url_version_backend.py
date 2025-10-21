"""
PEP 508 URL + Version Workaround Backend

This build backend works around PEP 508's limitation that you cannot specify
both a version constraint AND a git URL for the same dependency.

It provides automatic fallback:
- If custom index is configured: Use version constraints (fast, no git clones)
- If custom index NOT configured: Use git URLs (slow, but still works)

Usage in pyproject.toml:
    [build-system]
    requires = ["setuptools"]
    build-backend = "pep508_url_version_backend"
    backend-path = ["."]

    [project]
    name = "mypackage"
    version = "1.0.0"
    dependencies = []  # Leave empty, we populate dynamically

    [tool.pep508-url-version-backend]
    # Fast path - used when custom index is available
    dependencies-indexed = [
        "somepackage>=0.0.1234567",
    ]
    # Slow fallback - used when index not configured
    dependencies-git = [
        "somepackage @ git+https://github.com/user/somepackage",
    ]
    # Custom index URL to detect (optional, defaults below)
    index-urls = [
        "jakeogh.github.io",
        "myapps-index",
    ]
"""

import os
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

try:
    from tomlkit import parse as toml_parse, dumps as toml_dumps
except ImportError:
    # Fallback if tomlkit not available
    toml_parse = None
    toml_dumps = None

# Import the real setuptools backend
from setuptools import build_meta as _orig_backend


def _has_custom_index():
    """
    Check if a custom package index is configured.

    Checks:
    1. PIP_EXTRA_INDEX_URL environment variable
    2. PIP_INDEX_URL environment variable
    3. Known custom index URLs

    Returns:
        bool: True if custom index appears to be configured
    """
    # Check environment variables
    extra_index = os.environ.get('PIP_EXTRA_INDEX_URL', '')
    index_url = os.environ.get('PIP_INDEX_URL', '')

    # Load config to check for custom index markers
    config = _load_config()
    index_markers = config.get('index-urls', [
        'jakeogh.github.io',
        'myapps-index',
    ])

    # Check if any marker appears in the configured URLs
    for marker in index_markers:
        if marker in extra_index or marker in index_url:
            return True

    return False


def _load_config():
    """
    Load configuration from pyproject.toml.

    Returns:
        dict: Configuration from [tool.pep508-url-version-backend]
    """
    pyproject_path = Path('pyproject.toml')
    if not pyproject_path.exists():
        return {}

    with open(pyproject_path, 'rb') as f:
        data = tomllib.load(f)

    return data.get('tool', {}).get('pep508-url-version-backend', {})


def _get_dependencies():
    """
    Get the appropriate dependencies based on index configuration.

    Returns:
        list: List of dependency strings
    """
    config = _load_config()

    if _has_custom_index():
        # Fast path - use version constraints
        deps = config.get('dependencies-indexed', [])
        print(f"pep508_url_version_backend: Using indexed dependencies (fast path)",
              file=sys.stderr)
    else:
        # Slow fallback - use git URLs
        deps = config.get('dependencies-git', [])
        print(f"pep508_url_version_backend: Using git URL dependencies (slow fallback)",
              file=sys.stderr)
        print(f"pep508_url_version_backend: Set PIP_EXTRA_INDEX_URL to speed this up",
              file=sys.stderr)

    return deps


def _inject_dependencies():
    """
    Modify pyproject.toml in-place to inject the appropriate dependencies.

    This is called before the actual build to ensure setuptools sees
    the right dependencies.
    """
    pyproject_path = Path('pyproject.toml')

    if not pyproject_path.exists():
        return

    # Read with tomlkit to preserve formatting
    if toml_parse is None:
        print("WARNING: tomlkit not available, cannot inject dependencies",
              file=sys.stderr)
        return

    with open(pyproject_path) as f:
        doc = toml_parse(f.read())

    # Get the dependencies to inject
    deps = _get_dependencies()

    # Inject into [project] dependencies
    if 'project' not in doc:
        doc['project'] = {}

    doc['project']['dependencies'] = deps

    # Write back
    with open(pyproject_path, 'w') as f:
        f.write(toml_dumps(doc))


# Wrap all the PEP 517 hooks


def get_requires_for_build_wheel(config_settings=None):
    """PEP 517 hook: Get requirements for building a wheel."""
    return _orig_backend.get_requires_for_build_wheel(config_settings)


def get_requires_for_build_sdist(config_settings=None):
    """PEP 517 hook: Get requirements for building an sdist."""
    return _orig_backend.get_requires_for_build_sdist(config_settings)


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    """
    PEP 517 hook: Prepare metadata for wheel build.

    This is where we inject the appropriate dependencies before setuptools
    generates the metadata.
    """
    # Inject dependencies based on index availability
    _inject_dependencies()

    # Call the real backend
    return _orig_backend.prepare_metadata_for_build_wheel(
        metadata_directory,
        config_settings
    )


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """PEP 517 hook: Build a wheel."""
    # Inject dependencies if not already done
    _inject_dependencies()

    return _orig_backend.build_wheel(
        wheel_directory,
        config_settings,
        metadata_directory
    )


def build_sdist(sdist_directory, config_settings=None):
    """PEP 517 hook: Build an sdist."""
    # Inject dependencies
    _inject_dependencies()

    return _orig_backend.build_sdist(sdist_directory, config_settings)


# Optional PEP 660 hooks for editable installs
def get_requires_for_build_editable(config_settings=None):
    """PEP 660 hook: Get requirements for editable install."""
    if hasattr(_orig_backend, 'get_requires_for_build_editable'):
        return _orig_backend.get_requires_for_build_editable(config_settings)
    return []


def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    """PEP 660 hook: Prepare metadata for editable install."""
    # Inject dependencies
    _inject_dependencies()

    if hasattr(_orig_backend, 'prepare_metadata_for_build_editable'):
        return _orig_backend.prepare_metadata_for_build_editable(
            metadata_directory,
            config_settings
        )
    # Fallback to regular wheel metadata
    return prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    """PEP 660 hook: Build an editable wheel."""
    # Inject dependencies
    _inject_dependencies()

    if hasattr(_orig_backend, 'build_editable'):
        return _orig_backend.build_editable(
            wheel_directory,
            config_settings,
            metadata_directory
        )
    # Fallback to regular wheel
    return build_wheel(wheel_directory, config_settings, metadata_directory)
