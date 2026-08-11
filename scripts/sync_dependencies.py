import re
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

try:
    import tomli_w
except ModuleNotFoundError:
    # Fallback to plain toml dump if tomli_w is unavailable. tomli_w is a
    # tiny pure-Python writer; pip install tomli_w to preserve key order.
    try:
        import toml as _toml  # type: ignore
        class _FallbackWriter:
            @staticmethod
            def dump(obj, fp):
                _toml.dump(obj, fp)
        tomli_w = _FallbackWriter  # type: ignore
    except ModuleNotFoundError:
        print(
            "ERROR: sync_dependencies.py needs tomli_w (or the 'toml' package)\n"
            "       pip install tomli_w",
            file=sys.stderr,
        )
        raise


REQUIREMENTS_FILE = Path(__file__).resolve().parent.parent / "requirements.txt"
PYPROJECT_FILE = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _parse_requirements(path: Path) -> list[str]:
    specs: list[str] = []
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    for raw in raw_lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Strip any trailing inline comment, but keep the requirement spec
        head = re.split(r"\s+#", line, maxsplit=1)[0].strip()
        if head:
            specs.append(head)
    return specs


def sync() -> None:
    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError(f"requirements.txt not found at {REQUIREMENTS_FILE}")
    if not PYPROJECT_FILE.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {PYPROJECT_FILE}")

    specs = _parse_requirements(REQUIREMENTS_FILE)
    if not specs:
        print("WARNING: requirements.txt yielded zero dependency specs — aborting sync.",
              file=sys.stderr)
        raise SystemExit(2)

    with PYPROJECT_FILE.open("rb") as f:
        data = tomllib.load(f)

    project = data.setdefault("project", {})
    project["dependencies"] = specs

    with PYPROJECT_FILE.open("wb") as f:
        tomli_w.dump(data, f)

    print(f"Synced {len(specs)} dependency entries from requirements.txt -> pyproject.toml:project.dependencies")
    for s in specs:
        print(f"  - {s}")


if __name__ == "__main__":
    sync()

