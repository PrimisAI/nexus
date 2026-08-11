import os
from pathlib import Path
from setuptools import setup 

def _read_dependencies():
    """Single source of truth: pyproject.toml. Fallback to requirements.txt.

    Reads dependencies from pyproject.toml so there is only one
    place to update dependency versions. requirements.txt is
    only consulted if pyproject.toml is missing.
    """
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    if pyproject_path.exists():
        try:
            try:
                import tomllib  
            except ModuleNotFoundError:
                import tomli as tomllib  # type: ignore
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)
            deps = data.get("project", {}).get("dependencies")
            if isinstance(deps, list) and deps:
                return deps
        except Exception:
            pass

    requirements_path = Path(__file__).parent / "requirements.txt"
    if requirements_path.exists():
        with requirements_path.open("r", encoding="utf-8") as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
    return []


requirements = _read_dependencies()

setup(install_requires=requirements)

