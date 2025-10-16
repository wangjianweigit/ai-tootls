from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, Dict
from pathlib import Path
import logging
import os
from dotenv import load_dotenv, dotenv_values
import re


class Settings(BaseSettings):
	ragflow_base_url: Optional[str] = Field(default=None, validation_alias="RAGFLOW_BASE_URL")
	ragflow_api_key: Optional[str] = Field(default=None, validation_alias="RAGFLOW_API_KEY")

	fallback_openai_base_url: Optional[str] = Field(default=None, validation_alias="FALLBACK_OPENAI_BASE_URL")
	fallback_openai_api_key: Optional[str] = Field(default=None, validation_alias="FALLBACK_OPENAI_API_KEY")

	model: Optional[str] = Field(default=None, validation_alias="MODEL")
	fallback_model: Optional[str] = Field(default=None, validation_alias="FALLBACK_MODEL")

	# Kimi (Moonshot) provider
	kimi_base_url: Optional[str] = Field(default=None, validation_alias="KIMI_URL")
	kimi_api_key: Optional[str] = Field(default=None, validation_alias="KIMI_KEY")
	kimi_model: Optional[str] = Field(default=None, validation_alias="KIMI_MODEL")

	# Qwen (DashScope OpenAI-compatible)
	qwen_base_url: Optional[str] = Field(default=None, validation_alias="QWEN_URL")
	qwen_api_key: Optional[str] = Field(default=None, validation_alias="QWEN_KEY")
	qwen_model: Optional[str] = Field(default=None, validation_alias="QWEN_MODEL")

	# Doubao (Volc Ark)
	doubao_base_url: Optional[str] = Field(default=None, validation_alias="DOUBAO_BASE_URL")
	doubao_api_key: Optional[str] = Field(default=None, validation_alias="DOUBAO_API_KEY")
	doubao_model: Optional[str] = Field(default=None, validation_alias="DOUBAO_MODEL")

	# Database configuration
	database_url: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")
	sqlite_path: Optional[str] = Field(default=None, validation_alias="SQLITE_PATH")

	# HTTP timeout (seconds) for upstream model requests
	http_timeout_seconds: int = Field(default=600, validation_alias="HTTP_TIMEOUT_SECONDS")

	prompt_path: Path = Field(default=Path(__file__).resolve().parent.parent / "config" / "prompt.txt")

	# pydantic v2 configuration
	model_config = {
		"env_file": str(Path(__file__).resolve().parent.parent / ".env"),
		"env_file_encoding": "utf-8",
		"case_sensitive": True,
	}


# Ensure .env is loaded into process env first (for alias fallbacks like KIMI_URL)
_DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"
try:
	load_dotenv(dotenv_path=_DOTENV_PATH)
except Exception:
	pass

settings = Settings()

# Apply alias fallbacks for non-standard env var names
_DOTENV_VALUES = {}
try:
	_DOTENV_VALUES = dotenv_values(_DOTENV_PATH)
except Exception:
	_DOTENV_VALUES = {}

# Stronger fallback: parse .env manually and normalize keys (strip BOM/ZWSP/whitespace)
def _load_env_fallback_strict(path: Path):
	try:
		text = path.read_text(encoding="utf-8")
	except Exception:
		return {}
	zwsp = "\ufeff\u200b\u200c\u200d\u00a0"
	key_map: Dict[str, str] = {}
	for raw in text.splitlines():
		s = raw.strip()
		if not s or s.startswith("#"):
			continue
		if "=" not in s:
			continue
		k, v = s.split("=", 1)
		k = k.strip()
		# remove BOM/ZWSP/non-breaking space from key
		k = re.sub(f"[{zwsp}]", "", k)
		v = v.strip().strip('"').strip("'")
		key_map[k] = v
	return key_map

_STRICT_ENV = _load_env_fallback_strict(_DOTENV_PATH)

def _coalesce(*names: str) -> Optional[str]:
	for n in names:
		v = os.getenv(n)
		if not v and _DOTENV_VALUES:
			v = _DOTENV_VALUES.get(n)
		if not v and _STRICT_ENV:
			v = _STRICT_ENV.get(n)
		if v:
			return v
	return None

settings.kimi_base_url = settings.kimi_base_url or _coalesce("KIMI_URL", "KIMI_BASE_URL")
settings.kimi_api_key = settings.kimi_api_key or _coalesce("KIMI_KEY", "KIMI_API_KEY")
settings.kimi_model = settings.kimi_model or _coalesce("KIMI_MODEL")

settings.qwen_base_url = settings.qwen_base_url or _coalesce("QWEN_URL", "DASHSCOPE_BASE_URL")
settings.qwen_api_key = settings.qwen_api_key or _coalesce("QWEN_KEY", "DASHSCOPE_API_KEY")
settings.qwen_model = settings.qwen_model or _coalesce("QWEN_MODEL")

settings.doubao_base_url = settings.doubao_base_url or _coalesce("DOUBAO_BASE_URL", "ARK_BASE_URL")
settings.doubao_api_key = settings.doubao_api_key or _coalesce("DOUBAO_API_KEY", "ARK_API_KEY")
settings.doubao_model = settings.doubao_model or _coalesce("DOUBAO_MODEL")

# Database fallbacks
settings.database_url = settings.database_url or _coalesce("DATABASE_URL")
settings.sqlite_path = settings.sqlite_path or _coalesce("SQLITE_PATH", "DB_PATH")

# HTTP timeout fallback/coalesce and normalization
_timeout_val = _coalesce("HTTP_TIMEOUT_SECONDS", "HTTP_TIMEOUT", "REQUEST_TIMEOUT_SECONDS")
try:
	if _timeout_val:
		settings.http_timeout_seconds = int(str(_timeout_val).strip())
except Exception:
	pass

# debug prints for which keys were resolved (no secrets printed)
print("[config] resolved keys:", {
	"KIMI_URL": bool(settings.kimi_base_url),
	"QWEN_URL": bool(settings.qwen_base_url),
	"DOUBAO_BASE_URL": bool(settings.doubao_base_url),
})
try:
	print("[config] dotenv keys:", sorted(list(_DOTENV_VALUES.keys())))
	print("[config] strict keys:", sorted(list(_STRICT_ENV.keys())))
except Exception:
	pass

# logging summary (avoid printing secrets)
_logger = logging.getLogger("app.config")
try:
	_env = Path(__file__).resolve().parent.parent / ".env"
	_exists = _env.exists()
	# print for visibility regardless of logging configuration
	print(f"[config] env_file={_env} exists={_exists}")
	_logger.info(
		"Loaded settings from env_file=%s exists=%s",
		_env,
		_exists,
	)

	_logger.info(
		"Configured providers availability - ragflow=%s, kimi=%s, qwen=%s, doubao=%s, fallback=%s",
		bool(settings.ragflow_base_url and settings.ragflow_api_key and settings.model),
		bool(settings.kimi_base_url and settings.kimi_api_key and settings.kimi_model),
		bool(settings.qwen_base_url and settings.qwen_api_key and settings.qwen_model),
		bool(settings.doubao_base_url and settings.doubao_api_key and settings.doubao_model),
		bool(settings.fallback_openai_base_url and settings.fallback_openai_api_key and (settings.fallback_model or settings.model)),
	)
	print(
		"[config] available:",
		{
			"ragflow": bool(settings.ragflow_base_url and settings.ragflow_api_key and settings.model),
			"kimi": bool(settings.kimi_base_url and settings.kimi_api_key and settings.kimi_model),
			"qwen": bool(settings.qwen_base_url and settings.qwen_api_key and settings.qwen_model),
			"doubao": bool(settings.doubao_base_url and settings.doubao_api_key and settings.doubao_model),
			"fallback": bool(settings.fallback_openai_base_url and settings.fallback_openai_api_key and (settings.fallback_model or settings.model)),
		},
	)

	# also log non-secret visible fields for quick diagnosis
	_logger.info(
		"ragflow_base_url=%s model=%s; kimi_base_url=%s model=%s; qwen_base_url=%s model=%s; doubao_base_url=%s model=%s",
		settings.ragflow_base_url,
		settings.model,
		settings.kimi_base_url,
		settings.kimi_model,
		settings.qwen_base_url,
		settings.qwen_model,
		settings.doubao_base_url,
		settings.doubao_model,
	)
	print(
		"[config] urls:",
		{
			"ragflow_base_url": settings.ragflow_base_url,
			"model": settings.model,
			"kimi_base_url": settings.kimi_base_url,
			"kimi_model": settings.kimi_model,
			"qwen_base_url": settings.qwen_base_url,
			"qwen_model": settings.qwen_model,
			"doubao_base_url": settings.doubao_base_url,
			"doubao_model": settings.doubao_model,
			"database_url": settings.database_url,
			"sqlite_path": settings.sqlite_path,
			"http_timeout_seconds": settings.http_timeout_seconds,
		},
	)
except Exception as _e:  # best-effort logging only
	try:
		_logger.warning("Settings logging failed: %s", _e)
	except Exception:
		pass
