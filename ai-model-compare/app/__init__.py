from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import urlparse
from .config import settings

__all__ = [
	"config",
	"clients",
	"formatting",
	"main",
]

def _resolve_db_path() -> Path:
	# Priority: DATABASE_URL (sqlite) > SQLITE_PATH > default data/history.sqlite3
	if settings.database_url:
		url = settings.database_url.strip()
		if url.startswith("sqlite://"):
			# Accept forms: sqlite:///absolute/path.db or sqlite://relative/path.db
			o = urlparse(url)
			p = (o.path or "").lstrip("/") if o.netloc else (o.path or "").lstrip("/")
			if url.startswith("sqlite:////"):
				# explicit absolute path
				p = "/" + (o.path or "").lstrip("/")
			return Path(p).expanduser().resolve()
		elif url.startswith("file:"):
			# file:/absolute/path.db or file:///absolute/path.db
			raw = url.split(":", 1)[1]
			p = raw.lstrip("/")
			if raw.startswith("///"):
				p = "/" + raw.lstrip("/")
			return Path(p).expanduser().resolve()
	# fallback: explicit sqlite path
	if settings.sqlite_path:
		return Path(settings.sqlite_path).expanduser().resolve()
	# default
	return Path(__file__).resolve().parent.parent / "data" / "history.sqlite3"

DB_PATH = _resolve_db_path()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db():
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	return conn


def init_db() -> None:
	conn = get_db()
	cur = conn.cursor()
	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS history (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			created_at DATETIME DEFAULT (datetime('now','localtime')),
			filename TEXT,
			prompt TEXT,
			kimi_json TEXT,
			qwen_json TEXT,
			doubao_json TEXT,
			image_b64 TEXT
		);
		"""
	)

	# models table: store per-provider credentials and model info for UI selection
	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS models (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			provider TEXT NOT NULL,
			label TEXT,
			base_url TEXT NOT NULL,
			api_key TEXT NOT NULL,
			model TEXT NOT NULL,
			enabled INTEGER NOT NULL DEFAULT 1
		);
		"""
	)
	cur.execute("CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider)")

	# lightweight migration: add image_b64 column if missing
	try:
		cur.execute("PRAGMA table_info(history)")
		cols = {row[1] for row in cur.fetchall()}
		if "image_b64" not in cols:
			cur.execute("ALTER TABLE history ADD COLUMN image_b64 TEXT")
			conn.commit()
		if "results_json" not in cols:
			cur.execute("ALTER TABLE history ADD COLUMN results_json TEXT")
			conn.commit()
	except Exception:
		pass

	# sanity checks for models table columns (future-safe)
	try:
		cur.execute("PRAGMA table_info(models)")
		_ = cur.fetchall()
	except Exception:
		pass
	conn.commit()
	conn.close()


init_db()

