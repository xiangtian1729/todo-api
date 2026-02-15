import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def _run_alembic(database_url: str, *args: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=ROOT_DIR,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_migration_smoke_upgrade_downgrade_upgrade(tmp_path):
    db_path = tmp_path / "migration_smoke.db"
    database_url = f"sqlite+aiosqlite:///{db_path.as_posix()}"

    _run_alembic(database_url, "upgrade", "head")
    _run_alembic(database_url, "downgrade", "-1")
    _run_alembic(database_url, "upgrade", "head")
