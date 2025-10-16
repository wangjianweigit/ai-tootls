from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple
import json
import asyncio
from time import perf_counter

import httpx

from .config import settings
import logging
from .formatting import normalize_single_line


def _load_prompt_text() -> str:
	return Path(settings.prompt_path).read_text(encoding="utf-8").strip()


async def call_ragflow_with_image(image_bytes: bytes, filename: str) -> str:
	"""Call RagFlow (or compatible) to analyze the image and return single-line result.

	Strategy:
	1) Prefer RagFlow endpoint if configured; else fallback to OpenAI-compatible endpoint.
	2) We send a system prompt from prompt.txt and a user message with the image.
	"""
	system_prompt = _load_prompt_text()

	# Prefer RagFlow
	if settings.ragflow_base_url and settings.ragflow_api_key and settings.model:
		try:
			return await _call_openai_like(
				base_url=settings.ragflow_base_url,
				api_key=settings.ragflow_api_key,
				model=settings.model,
				image_bytes=image_bytes,
				filename=filename,
				system_prompt=system_prompt,
			)
		except Exception:
			pass

	# Fallback
	if settings.fallback_openai_base_url and settings.fallback_openai_api_key and (settings.fallback_model or settings.model):
		model = settings.fallback_model or settings.model
		return await _call_openai_like(
			base_url=settings.fallback_openai_base_url,
			api_key=settings.fallback_openai_api_key,
			model=model,
			image_bytes=image_bytes,
			filename=filename,
			system_prompt=system_prompt,
		)

	raise RuntimeError("No RagFlow or fallback OpenAI-compatible endpoint configured")


async def _call_openai_like(
	base_url: str,
	api_key: str,
	model: str,
	image_bytes: bytes,
	filename: str,
	system_prompt: str,
) -> str:
	"""Call an OpenAI-compatible chat.completions API that supports image_url/base64."""
	# We encode the image as base64 data URL
	b64 = base64.b64encode(image_bytes).decode("utf-8")
	data_url = f"data:image/{_suffix_of(filename)};base64,{b64}"

	# 合并 system_prompt 到 user 消息中，因为某些本地部署可能不支持 system 角色
	user_text = "请分析图片并按要求输出"
	if system_prompt:
		user_text = f"{system_prompt}\n\n{user_text}"

	payload: Dict[str, Any] = {
		"model": model,
		"messages": [
			{
				"role": "user",
				"content": [
					{"type": "text", "text": user_text},
					{"type": "image_url", "image_url": {"url": data_url}},
				],
			},
		],
		"temperature": 0,
		"max_tokens": 4096,
	}

	headers = {
		"Authorization": f"Bearer {api_key}",
		"Content-Type": "application/json",
		"Accept": "application/json",
	}

	async with httpx.AsyncClient(base_url=base_url, timeout=settings.http_timeout_seconds) as client:
		lower = (base_url or "").lower()
		if "aistarfish.net" in lower:
			# 本地网关要求 Authorization Bearer 及可能的 X-API-Key
			headers["Authorization"] = f"Bearer {api_key}"
			headers.setdefault("X-API-Key", api_key)
		if "compatible-mode" in lower or "dashscope.aliyuncs.com" in lower:
			path_candidates: List[str] = [
				"/chat/completions",
			]
		elif "aistarfish.net" in lower:
			path_candidates = [
				"/v1/chat/completions",
			]
		elif "volces.com" in lower or "/api/v3" in lower:
			path_candidates = [
				"/chat/completions",
			]
		elif "moonshot.cn" in lower:
			path_candidates = [
				"/v1/chat/completions",
				"/chat/completions",
			]
		else:
			path_candidates = [
				"/v1/chat/completions",
				"/chat/completions",
				"/openai/v1/chat/completions",
			]
		last_error: Optional[Exception] = None
		for path in path_candidates:
			try:
				_log_outgoing_request(lower, path, headers, payload)
				resp = await client.post(path, json=payload, headers=headers)
				resp.raise_for_status()
				data = resp.json()
				text: Optional[str] = None
				if isinstance(data, dict):
					choices = data.get("choices")
					if isinstance(choices, list) and choices:
						message = choices[0].get("message")
						if isinstance(message, dict):
							text = message.get("content")
				if not text:
					raise RuntimeError("Empty response from model")
				return normalize_single_line("".join(str(text).splitlines()).strip())
			except Exception as e:
				try:
					_log_failed_response(lower, path, e, locals().get("resp"), headers)
				except Exception:
					pass
				last_error = e
				continue
		raise RuntimeError(f"No compatible chat.completions path succeeded: {last_error}")


async def _call_openai_like_with_user_text(
	base_url: str,
	api_key: str,
	model: str,
	image_bytes: bytes,
	filename: str,
	system_prompt: str,
	user_text: str,
) -> str:
	"""Same as _call_openai_like but allows custom user text in addition to image."""
	b64 = base64.b64encode(image_bytes).decode("utf-8")
	data_url = f"data:image/{_suffix_of(filename)};base64,{b64}"

	# 合并 system_prompt 和 user_text，因为某些本地部署可能不支持 system 角色
	combined_text = user_text or "请分析图片并按要求输出"
	if system_prompt:
		combined_text = f"{system_prompt}\n\n{combined_text}"

	payload: Dict[str, Any] = {
		"model": model,
		"messages": [
			{
				"role": "user",
				"content": [
					{"type": "text", "text": combined_text},
					{"type": "image_url", "image_url": {"url": data_url}},
				],
			},
		],
		"temperature": 0,
		"max_tokens": 4096,
	}

	headers = {
		"Authorization": f"Bearer {api_key}",
		"Content-Type": "application/json",
		"Accept": "application/json",
	}

	async with httpx.AsyncClient(base_url=base_url, timeout=settings.http_timeout_seconds) as client:
		lower = (base_url or "").lower()
		
		# 根据 base_url 确定路径候选列表
		if "compatible-mode" in lower or "dashscope.aliyuncs.com" in lower:
			# DashScope 的 compatible-mode 已经包含完整路径，只需要 /chat/completions
			path_candidates: List[str] = [
				"/chat/completions",
			]
		elif "volces.com" in lower or "/api/v3" in lower:
			# Doubao (字节火山引擎)
			path_candidates = [
				"/chat/completions",
			]
		elif "moonshot.cn" in lower:
			# Kimi (Moonshot AI)
			path_candidates = [
				"/v1/chat/completions",
				"/chat/completions",
			]
		else:
			# 通用 OpenAI-compatible 端点（包括本地部署）
			path_candidates = [
				"/v1/chat/completions",
				"/chat/completions",
				"/openai/v1/chat/completions",
			]
		last_error: Optional[Exception] = None
		error_details = []
		for path in path_candidates:
			try:
				_log_outgoing_request(lower, path, headers, payload)
				resp = await client.post(path, json=payload, headers=headers)
				resp.raise_for_status()
				data = resp.json()
				text: Optional[str] = None
				if isinstance(data, dict):
					choices = data.get("choices")
					if isinstance(choices, list) and choices:
						message = choices[0].get("message")
						if isinstance(message, dict):
							text = message.get("content")
				if not text:
					raise RuntimeError("Empty response from model")
				return normalize_single_line("".join(str(text).splitlines()).strip())
			except Exception as e:
				_log_failed_response(lower, path, e, locals().get("resp"), headers)
				last_error = e
				error_details.append((path, type(e).__name__, str(e)))
				continue
		
		# Only log detailed error after all paths have failed
		if error_details:
			logger = logging.getLogger("app.http")
			logger.error(f"All API paths failed for {base_url}. Tried {len(error_details)} path(s):")
			for path, err_type, err_msg in error_details:
				logger.error(f"  - {path}: {err_type}")
			# Log network issue only once if it's a connection problem
			if last_error and isinstance(last_error, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)):
				logger.error(f"Network issue: Cannot reach {base_url} - please check if the server is accessible")
		
		raise RuntimeError(f"No compatible chat.completions path succeeded: {last_error}")


async def compare_multiple_models(
	image_bytes: bytes,
	filename: str,
	user_prompt: str,
	model_configs: List[Dict[str, Any]],
) -> Dict[str, Any]:
	"""Call multiple models concurrently and return results.

	Args:
		image_bytes: Image data
		filename: Image filename
		user_prompt: User's prompt text
		model_configs: List of model configs, each with keys: id, provider, label, base_url, api_key, model

	Returns:
		Dict mapping model_id (as string) -> { ok: bool, text|error, elapsed_ms, provider, label }
	"""
	system_prompt = _load_prompt_text()
	logger = logging.getLogger("app.compare")
	logger.info(f"compare_multiple_models: {len(model_configs)} models")

	async def _wrap(model_id: int, provider: str, label: str, base_url: str, api_key: str, model: str) -> Dict[str, Any]:
		start = perf_counter()
		try:
			text = await _call_openai_like_with_user_text(
				base_url=base_url,
				api_key=api_key,
				model=model,
				image_bytes=image_bytes,
				filename=filename,
				system_prompt=system_prompt,
				user_text=user_prompt,
			)
			elapsed = int((perf_counter() - start) * 1000)
			return {
				"ok": True,
				"text": text,
				"elapsed_ms": elapsed,
				"provider": provider,
				"label": label,
				"model": model,
			}
		except Exception as e:
			elapsed = int((perf_counter() - start) * 1000)
			return {
				"ok": False,
				"error": str(e),
				"elapsed_ms": elapsed,
				"provider": provider,
				"label": label,
				"model": model,
			}

	# Create tasks for all models
	tasks = []
	for cfg in model_configs:
		model_id = cfg["id"]
		provider = cfg["provider"]
		label = cfg.get("label") or cfg["model"]
		base_url = cfg["base_url"]
		api_key = cfg["api_key"]
		model = cfg["model"]
		
		task = asyncio.create_task(_wrap(model_id, provider, label, base_url, api_key, model))
		tasks.append((str(model_id), task))

	if not tasks:
		return {}

	# Wait for all tasks to complete
	done = await asyncio.gather(*[t for _, t in tasks])
	
	# Build results dict
	results = {}
	for (model_id, _), res in zip(tasks, done):
		results[model_id] = res

	return results


async def compare_across_providers(
	image_bytes: bytes,
	filename: str,
	user_prompt: str,
	provider_overrides: Optional[Dict[str, Dict[str, str]]] = None,
) -> Dict[str, Any]:
	"""Call all configured providers (Kimi, Qwen, Doubao) concurrently and return results.

	Returns a dict mapping provider -> { ok: bool, text|error, elapsed_ms }.
	"""
	system_prompt = _load_prompt_text()
	logger = logging.getLogger("app.compare")
	logger.info(
		"compare start: kimi=%s qwen=%s doubao=%s",
		bool(settings.kimi_base_url and settings.kimi_api_key and settings.kimi_model),
		bool(settings.qwen_base_url and settings.qwen_api_key and settings.qwen_model),
		bool(settings.doubao_base_url and settings.doubao_api_key and settings.doubao_model),
	)

	tasks: List[Tuple[str, asyncio.Task]] = []
	results: Dict[str, Any] = {}

	async def _wrap(provider: str, base_url: str, api_key: str, model: str) -> Dict[str, Any]:
		start = perf_counter()
		try:
			text = await _call_openai_like_with_user_text(
				base_url=base_url,
				api_key=api_key,
				model=model,
				image_bytes=image_bytes,
				filename=filename,
				system_prompt=system_prompt,
				user_text=user_prompt,
			)
			elapsed = int((perf_counter() - start) * 1000)
			return {"ok": True, "text": text, "elapsed_ms": elapsed}
		except Exception as e:
			elapsed = int((perf_counter() - start) * 1000)
			return {"ok": False, "error": str(e), "elapsed_ms": elapsed}

	# Kimi (allow override)
	kimi_cfg = None
	if provider_overrides and provider_overrides.get("kimi"):
		cfg = provider_overrides["kimi"]
		kimi_cfg = (cfg.get("base_url"), cfg.get("api_key"), cfg.get("model"))
	elif settings.kimi_base_url and settings.kimi_api_key and settings.kimi_model:
		kimi_cfg = (settings.kimi_base_url, settings.kimi_api_key, settings.kimi_model)
	if kimi_cfg and all(kimi_cfg):
		tasks.append((
			"kimi",
			asyncio.create_task(_wrap("kimi", kimi_cfg[0], kimi_cfg[1], kimi_cfg[2])),
		))
	else:
		results["kimi"] = {"ok": False, "error": "not configured"}

	# Qwen (allow override)
	qwen_cfg = None
	if provider_overrides and provider_overrides.get("qwen"):
		cfg = provider_overrides["qwen"]
		qwen_cfg = (cfg.get("base_url"), cfg.get("api_key"), cfg.get("model"))
	elif settings.qwen_base_url and settings.qwen_api_key and settings.qwen_model:
		qwen_cfg = (settings.qwen_base_url, settings.qwen_api_key, settings.qwen_model)
	if qwen_cfg and all(qwen_cfg):
		tasks.append((
			"qwen",
			asyncio.create_task(_wrap("qwen", qwen_cfg[0], qwen_cfg[1], qwen_cfg[2])),
		))
	else:
		results["qwen"] = {"ok": False, "error": "not configured"}

	# Doubao (allow override)
	doubao_cfg = None
	if provider_overrides and provider_overrides.get("doubao"):
		cfg = provider_overrides["doubao"]
		doubao_cfg = (cfg.get("base_url"), cfg.get("api_key"), cfg.get("model"))
	elif settings.doubao_base_url and settings.doubao_api_key and settings.doubao_model:
		doubao_cfg = (settings.doubao_base_url, settings.doubao_api_key, settings.doubao_model)
	if doubao_cfg and all(doubao_cfg):
		tasks.append((
			"doubao",
			asyncio.create_task(_wrap("doubao", doubao_cfg[0], doubao_cfg[1], doubao_cfg[2])),
		))
	else:
		results["doubao"] = {"ok": False, "error": "not configured"}

	if not tasks:
		return results

	done = await asyncio.gather(*[t for _, t in tasks])
	for (name, _), res in zip(tasks, done):
		results[name] = res

	return results


def _suffix_of(filename: str) -> str:
	suffix = Path(filename).suffix.lower().lstrip(".")
	if suffix in {"jpg", "jpeg", "png", "gif", "webp", "bmp"}:
		return suffix
	return "jpeg"


def _mask(s: Optional[str]) -> str:
	if not s:
		return ""
	if len(s) <= 8:
		return "***"
	return s[:8] + "***"


def _sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
	try:
		cloned = json.loads(json.dumps(payload))
		for msg in cloned.get("messages", []):
			if isinstance(msg, dict) and isinstance(msg.get("content"), list):
				for part in msg["content"]:
					if isinstance(part, dict) and part.get("type") == "image_url":
						url = part.get("image_url", {}).get("url")
						if isinstance(url, str) and url.startswith("data:image/"):
							part["image_url"]["url"] = "data:image/...;base64,<<omitted>>"
		return cloned
	except Exception:
		return {"error": "sanitize_failed"}


def _log_outgoing_request(lower_base_url: str, path: str, headers: Dict[str, str], payload: Dict[str, Any]) -> None:
	logger = logging.getLogger("app.http")
	masked_headers = {**headers}
	if "Authorization" in masked_headers:
		masked_headers["Authorization"] = "Bearer " + _mask(headers.get("Authorization", "").replace("Bearer ", ""))
	
	# 打印完整的请求信息
	logger.info("=" * 80)
	logger.info("HTTP POST Request Details:")
	logger.info(f"  URL: {lower_base_url}{path}")
	logger.info(f"  Headers:")
	for key, value in masked_headers.items():
		logger.info(f"    {key}: {value}")
	logger.info(f"  Payload: {_sanitize_payload(payload)}")
	logger.info("=" * 80)


def _log_failed_response(lower_base_url: str, path: str, err: Exception, resp: Any, headers: Dict[str, str] = None) -> None:
	logger = logging.getLogger("app.http")
	try:
		status = getattr(resp, "status_code", None)
		text = None
		if hasattr(resp, "text"):
			text = resp.text[:500] if resp.text else None  # 限制长度
		error_type = type(err).__name__
		
		# 打印详细的失败信息
		logger.warning("=" * 80)
		logger.warning("HTTP Request FAILED:")
		logger.warning(f"  URL: {lower_base_url}{path}")
		if headers:
			masked_headers = {**headers}
			if "Authorization" in masked_headers:
				masked_headers["Authorization"] = "Bearer " + _mask(headers.get("Authorization", "").replace("Bearer ", ""))
			logger.warning(f"  Headers:")
			for key, value in masked_headers.items():
				logger.warning(f"    {key}: {value}")
		logger.warning(f"  Status Code: {status}")
		logger.warning(f"  Error Type: {error_type}")
		logger.warning(f"  Error Message: {err}")
		if text:
			logger.warning(f"  Response Body: {text}")
		logger.warning("=" * 80)
	except Exception:
		error_type = type(err).__name__
		logger.warning("HTTP FAIL %s%s err_type=%s err=%s", lower_base_url, path, error_type, err)
