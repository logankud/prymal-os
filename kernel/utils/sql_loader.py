from pathlib import Path

# SQL files live at the repo root: /sql/**
SQL_BASE_PATH = Path(__file__).resolve().parents[2] / "sql"


def load_sql(relative_path: str) -> str:
    """Load a SQL file from the repo-level sql directory."""
    sql_path = SQL_BASE_PATH / relative_path

    with open(sql_path, "r", encoding="utf-8") as f:
        return f.read()
