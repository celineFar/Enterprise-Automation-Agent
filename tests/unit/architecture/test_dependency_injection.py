import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[3]
SOURCE_ROOT = PROJECT_ROOT / "src" / "agent_platform"
COMPOSITION_IMPORTS = {
    "agent_platform.bootstrap.application": {"create_application_container"},
    "agent_platform.bootstrap.container": {"ApplicationContainer"},
}
CONTAINER_BOUNDARIES = {
    SOURCE_ROOT / "api" / "app.py",
    SOURCE_ROOT / "api" / "dependencies.py",
    SOURCE_ROOT / "bootstrap" / "application.py",
    SOURCE_ROOT / "bootstrap" / "container.py",
    SOURCE_ROOT / "workers" / "main.py",
}


def test_application_container_is_confined_to_composition_boundaries() -> None:
    violations: list[str] = []

    for path in SOURCE_ROOT.rglob("*.py"):
        if path in CONTAINER_BOUNDARIES:
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name in COMPOSITION_IMPORTS for alias in node.names
            ):
                violations.append(str(path.relative_to(PROJECT_ROOT)))
            if (
                isinstance(node, ast.ImportFrom)
                and node.module in COMPOSITION_IMPORTS
                and any(alias.name in COMPOSITION_IMPORTS[node.module] for alias in node.names)
            ):
                violations.append(str(path.relative_to(PROJECT_ROOT)))

    assert not violations, (
        "ApplicationContainer may only be used at bootstrap, API, and worker boundaries; "
        f"inject narrow dependencies into consumers and handlers instead: {violations}"
    )
