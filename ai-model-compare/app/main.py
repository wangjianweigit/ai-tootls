from __future__ import annotations

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request, APIRouter
from fastapi.responses import PlainTextResponse, RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
import io
from pathlib import Path
import json

from .clients import call_ragflow_with_image, compare_across_providers
from . import get_db
from .formatting import normalize_single_line
from .config import settings

app = FastAPI(title="RagFlow Image Composition Classifier", version="0.1.0")

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 设置模板目录
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# 带统一前缀的路由器
_BASE_PREFIX = "/ai-model-compare"
router = APIRouter(prefix=_BASE_PREFIX)

@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
	return RedirectResponse(url="/docs")


@router.get("/health", response_class=PlainTextResponse)
async def health() -> str:
	return "ok"


@router.post("/analyze", response_class=PlainTextResponse)
async def analyze(file: UploadFile = File(...)) -> str:
	try:
		content = await file.read()
		# basic validation the content is image
		Image.open(io.BytesIO(content))
	except Exception:
		raise HTTPException(status_code=400, detail="Invalid image")

	try:
		result = await call_ragflow_with_image(content, file.filename)
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

	return normalize_single_line(result)


@router.get("/debug/config", response_class=JSONResponse)
async def debug_config() -> JSONResponse:
	data = {
		"env_file": str(__import__("pathlib").Path(__file__).resolve().parent.parent / ".env"),
		"ragflow": bool(settings.ragflow_base_url and settings.ragflow_api_key and settings.model),
		"kimi": bool(settings.kimi_base_url and settings.kimi_api_key and settings.kimi_model),
		"qwen": bool(settings.qwen_base_url and settings.qwen_api_key and settings.qwen_model),
		"doubao": bool(settings.doubao_base_url and settings.doubao_api_key and settings.doubao_model),
		"database": settings.database_url or str(settings.sqlite_path),
		"urls": {
			"ragflow_base_url": settings.ragflow_base_url,
			"kimi_base_url": settings.kimi_base_url,
			"qwen_base_url": settings.qwen_base_url,
			"doubao_base_url": settings.doubao_base_url,
		},
	}
	return JSONResponse(data)


@router.get("/history", response_class=JSONResponse)
async def history_list(limit: int = 20, offset: int = 0) -> JSONResponse:
	conn = get_db()
	try:
		cur = conn.cursor()
		cur.execute("SELECT id, created_at, filename, prompt FROM history ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
		rows = [dict(r) for r in cur.fetchall()]
	finally:
		conn.close()
	return JSONResponse({"items": rows})


@router.get("/history/{item_id}", response_class=JSONResponse)
async def history_detail(item_id: int) -> JSONResponse:
	conn = get_db()
	try:
		cur = conn.cursor()
		cur.execute("SELECT id, created_at, filename, prompt, kimi_json, qwen_json, doubao_json, image_b64 FROM history WHERE id=?", (item_id,))
		row = cur.fetchone()
		if not row:
			raise HTTPException(status_code=404, detail="not found")
		data = dict(row)
	finally:
		conn.close()
	return JSONResponse(data)


@router.get("/history/{item_id}/image")
async def history_image(item_id: int):
	from fastapi.responses import Response
	conn = get_db()
	try:
		cur = conn.cursor()
		cur.execute("SELECT image_b64, filename FROM history WHERE id=?", (item_id,))
		row = cur.fetchone()
		if not row:
			raise HTTPException(status_code=404, detail="not found")
		import base64
		image_bytes = base64.b64decode(row[0]) if row[0] else b""
		filename = row[1]
	finally:
		conn.close()
	return Response(content=image_bytes, media_type="application/octet-stream", headers={"Content-Disposition": f"inline; filename={filename}"})


@router.get("/history-ui", response_class=HTMLResponse)
async def history_ui(request: Request) -> HTMLResponse:
	"""对比历史 UI（使用模板渲染，方便统一注入导航）"""
	return templates.TemplateResponse("history.html", {"request": request})


@router.get("/models", response_class=JSONResponse)
async def list_models() -> JSONResponse:
	conn = get_db()
	try:
		cur = conn.cursor()
		cur.execute("SELECT id, created_at, provider, label, base_url, model, enabled FROM models ORDER BY id DESC")
		rows = [dict(r) for r in cur.fetchall()]
	finally:
		conn.close()
	return JSONResponse({"items": rows})


@router.post("/models", response_class=JSONResponse)
async def create_model(
	provider: str = Form(...),
	label: str = Form(""),
	base_url: str = Form(...),
	api_key: str = Form(...),
	model: str = Form(...),
	enabled: int = Form(1),
) -> JSONResponse:
	provider = provider.strip().lower()
	if provider not in {"kimi", "qwen", "doubao"}:
		raise HTTPException(status_code=400, detail="provider must be one of kimi/qwen/doubao")
	conn = get_db()
	try:
		cur = conn.cursor()
		cur.execute(
			"INSERT INTO models (provider, label, base_url, api_key, model, enabled) VALUES (?, ?, ?, ?, ?, ?)",
			(provider, label, base_url, api_key, model, int(bool(enabled))),
		)
		conn.commit()
		new_id = cur.lastrowid
	finally:
		conn.close()
	return JSONResponse({"id": new_id})


@router.delete("/models/{model_id}", response_class=JSONResponse)
async def delete_model(model_id: int) -> JSONResponse:
	conn = get_db()
	try:
		cur = conn.cursor()
		cur.execute("DELETE FROM models WHERE id=?", (model_id,))
		conn.commit()
	finally:
		conn.close()
	return JSONResponse({"ok": True})
@router.post("/compare", response_class=JSONResponse)
async def compare(
	file: UploadFile = File(...),
	prompt: str = Form(...),  # 必填字段
	model_ids: str = Form(""),
) -> JSONResponse:
	# 验证提示词不能为空
	if not prompt or not prompt.strip():
		raise HTTPException(status_code=400, detail="提示词不能为空，请输入分析要求")
	
	try:
		content = await file.read()
		Image.open(io.BytesIO(content))
	except Exception:
		raise HTTPException(status_code=400, detail="Invalid image")

	# Parse model_ids (comma-separated)
	import logging
	logger = logging.getLogger("app.compare")
	logger.info(f"Received model_ids: {repr(model_ids)}")
	
	model_id_list = [int(x.strip()) for x in model_ids.split(",") if x.strip().isdigit()] if model_ids else []
	logger.info(f"Parsed model_id_list: {model_id_list}")
	
	if not model_id_list:
		raise HTTPException(status_code=400, detail=f"No valid model IDs provided. Received: {repr(model_ids)}")

	# Load model configurations from database
	model_configs = []
	conn = get_db()
	try:
		cur = conn.cursor()
		for model_id in model_id_list:
			cur.execute("SELECT id, provider, label, base_url, api_key, model FROM models WHERE id=? AND enabled=1", (model_id,))
			row = cur.fetchone()
			if row:
				model_configs.append(dict(row))
	finally:
		conn.close()

	if not model_configs:
		raise HTTPException(status_code=400, detail="No valid models found")

	# Import the new comparison function
	from .clients import compare_multiple_models
	
	try:
		results = await compare_multiple_models(content, file.filename, prompt, model_configs)
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

	# Save history into sqlite (image base64)
	try:
		conn = get_db()
		cur = conn.cursor()
		import base64
		img_b64 = base64.b64encode(content).decode("utf-8")
		
		# Group results by provider for history storage
		grouped = {"kimi": None, "qwen": None, "doubao": None}
		for model_id, result in results.items():
			model_cfg = next((m for m in model_configs if m["id"] == int(model_id)), None)
			if model_cfg:
				provider = model_cfg["provider"]
				if provider in grouped and grouped[provider] is None:
					grouped[provider] = result
		
		cur.execute(
			"INSERT INTO history (filename, prompt, kimi_json, qwen_json, doubao_json, image_b64) VALUES (?, ?, ?, ?, ?, ?)",
			(
				file.filename,
				prompt,
				str(grouped.get("kimi")),
				str(grouped.get("qwen")),
				str(grouped.get("doubao")),
				img_b64,
			),
		)
		conn.commit()
		history_id = cur.lastrowid
	finally:
		try:
			conn.close()
		except Exception:
			pass

	payload = {"id": history_id, "results": results}
	return JSONResponse(payload)


@router.get("/ui")
async def ui(request: Request):
	"""多模态模型对比UI"""
	return templates.TemplateResponse("compare.html", {"request": request})


@router.get("/models-ui")
async def models_ui(request: Request):
	"""模型管理UI"""
	return templates.TemplateResponse("models.html", {"request": request})


@app.get("/integration-guide")
async def integration_guide(request: Request):
	"""开发者接入指南页面"""
	return templates.TemplateResponse("integration.html", {"request": request})


@router.get("/menus", response_class=JSONResponse)
async def menus() -> JSONResponse:
	"""返回"海心AI工具集"菜单配置，支持动态工具发现。
	
	优先级：
	1. 优先读取项目根目录的 tools.json（全局工具配置）
	2. 其次读取本地 config/menus.json（本地配置）
	3. 最后使用默认配置
	
	全局 tools.json 支持工具自动发现和注册
	"""
	# 尝试读取全局工具配置
	global_config_path = BASE_DIR.parent / "tools.json"
	# 本地配置路径
	local_config_path = BASE_DIR / "config" / "menus.json"
	
	default_payload = {
		"brand": {"title": "海心AI工具集", "link": f"{_BASE_PREFIX}/ui"},
		"tools": [
			{
				"id": "ai-model-compare",
				"name": "AI模型对比",
				"icon": "🤖",
				"description": "多模态AI模型对比工具",
				"pages": [
					{"key": "compare", "title": "模型对比", "path": f"{_BASE_PREFIX}/ui", "icon": "🔬"},
					{"key": "models", "title": "模型管理", "path": f"{_BASE_PREFIX}/models-ui", "icon": "⚙️"},
					{"key": "history", "title": "对比历史", "path": f"{_BASE_PREFIX}/history-ui", "icon": "📜"},
				]
			}
		]
	}
	
	try:
		# 优先读取全局配置
		if global_config_path.exists():
			data = json.loads(global_config_path.read_text(encoding="utf-8"))
			if isinstance(data, dict) and "tools" in data:
				# 只返回启用的工具
				enabled_tools = [t for t in data.get("tools", []) if t.get("enabled", True)]
				data["tools"] = enabled_tools
				data.setdefault("brand", default_payload["brand"])
				return JSONResponse(data)
		
		# 读取本地配置
		if local_config_path.exists():
			data = json.loads(local_config_path.read_text(encoding="utf-8"))
			if not isinstance(data, dict):
				return JSONResponse(default_payload)
			data.setdefault("brand", default_payload["brand"])
			tools = data.get("tools")
			if not isinstance(tools, list) or not tools:
				data["tools"] = default_payload["tools"]
			return JSONResponse(data)
	except Exception as e:
		# 记录错误但继续运行
		import logging
		logging.error(f"Failed to load menu config: {e}")
	
	return JSONResponse(default_payload)


# 前缀根路径重定向到 UI
@router.get("/", include_in_schema=False)
async def prefixed_root() -> RedirectResponse:
	return RedirectResponse(url=f"{_BASE_PREFIX}/ui")


# 将带前缀的路由器注册到应用
app.include_router(router)
