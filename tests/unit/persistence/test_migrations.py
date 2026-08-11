from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

PROJECT_ROOT = Path(__file__).parents[3]


def test_migration_chain_has_one_empty_baseline_head() -> None:
    config = Config(PROJECT_ROOT / "alembic.ini")
    scripts = ScriptDirectory.from_config(config)

    assert scripts.get_heads() == ["0001_initial_schema_baseline"]
    assert scripts.get_base() == "0001_initial_schema_baseline"


def test_application_does_not_create_or_drop_schema_directly() -> None:
    forbidden_operations = ("create_all(", "drop_all(")

    for source_file in (PROJECT_ROOT / "src").rglob("*.py"):
        source = source_file.read_text(encoding="utf-8")
        assert all(operation not in source for operation in forbidden_operations), source_file
