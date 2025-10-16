from __future__ import annotations

import json
from pathlib import Path

import sqlite3

# Reuse DB path resolution from app package if available
try:
    from app import get_db  # type: ignore
except Exception:
    get_db = None


def _fallback_db_path() -> Path:
    # Default path aligned with app/__init__.py
    return Path(__file__).resolve().parents[1] / "data" / "history.sqlite3"


def _open_conn() -> sqlite3.Connection:
    if get_db is not None:
        return get_db()
    db_path = _fallback_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def export_models(out_file: Path) -> None:
    conn = _open_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, created_at, provider, label, base_url, api_key, model, enabled
            FROM models
            ORDER BY id ASC
            """
        )
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        json.dump({"items": rows}, f, ensure_ascii=False, indent=2)
    print(f"Exported {len(rows)} models to {out_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export models table to JSON")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("models-export.json"),
        help="Output JSON file path",
    )
    args = parser.parse_args()
    export_models(args.out)


