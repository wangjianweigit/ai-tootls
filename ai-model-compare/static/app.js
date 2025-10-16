// 全局变量
let allModels = [];
const $ = (selector) => document.querySelector(selector);

// 文件选择处理
$('#file').addEventListener('change', (e) => {
	const file = e.target.files[0];
	const fileInfo = $('#file-info');
	if (file) {
		fileInfo.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
		fileInfo.style.color = 'var(--success-color)';
	} else {
		fileInfo.textContent = '未选择任何文件';
		fileInfo.style.color = 'var(--text-muted)';
	}
});

// 加载模型列表
const API_BASE = '/ai-model-compare';

async function loadModels() {
	const container = $('#model-selector');
	if (!container) return;

	// 显示加载状态
	container.innerHTML = `
		<div class="loading-state">
			<div class="spinner"></div>
			<span>加载中...</span>
		</div>
	`;

	try {
		const res = await fetch(API_BASE + '/models');
		if (!res.ok) throw new Error('获取模型列表失败');
		const data = await res.json();
		allModels = data.items || [];

		// 按 provider 分组
		const groups = { kimi: [], qwen: [], doubao: [] };
		allModels.filter(it => !!it && it.enabled).forEach(it => {
			if (groups[it.provider]) groups[it.provider].push(it);
		});

		// 构建复选框列表
		let html = '';
		const providerNames = {
			kimi: '🌙 Kimi 模型',
			qwen: '🧠 Qwen 模型',
			doubao: '🔥 Doubao 模型'
		};

		for (const [provider, models] of Object.entries(groups)) {
			if (models.length) {
				html += `<div class="model-group-title">${providerNames[provider]}</div>`;
				models.forEach(it => {
					html += `
						<div class="model-item">
							<input type="checkbox" id="model-${provider}-${it.id}" value="${provider}:${it.id}">
							<label for="model-${provider}-${it.id}">${it.label || it.model}</label>
						</div>
					`;
				});
			}
		}

		container.innerHTML = html || '<div class="loading-state"><span>暂无可用模型</span></div>';
	} catch (e) {
		console.error('loadModels failed', e);
		container.innerHTML = `
			<div class="loading-state">
				<span style="color: var(--error-color);">❌ 加载失败: ${e.message}</span>
			</div>
		`;
	}
}

// 刷新模型按钮
const btnRefresh = $('#refresh-models');
if (btnRefresh) {
	btnRefresh.onclick = loadModels;
}

// 运行对比
$('#run').onclick = async () => {
	const fileInput = $('#file');
	const f = fileInput.files[0];
	const prompt = $('#prompt').value || '';

	if (!f) {
		alert('⚠️ 请先选择图片');
		return;
	}

	// 获取所有选中的复选框
	const checkboxes = document.querySelectorAll('#model-selector input[type="checkbox"]:checked');
	const selected = Array.from(checkboxes).map(cb => cb.value);
	
	if (!selected.length) {
		alert('⚠️ 请至少选择一个模型');
		return;
	}

	const runBtn = $('#run');
	const status = $('#status');
	
	runBtn.disabled = true;
	status.textContent = '正在处理...';
	status.style.color = 'var(--primary-color)';

	// 动态创建结果面板
	const resultsDiv = $('#results');
	resultsDiv.innerHTML = selected.map(v => {
		const [provider, id] = v.split(':');
		const model = allModels.find(m => m.id == parseInt(id));
		const label = model ? (model.label || model.model) : provider;
		const providerIcons = { kimi: '🌙', qwen: '🧠', doubao: '🔥' };
		const icon = providerIcons[provider] || '🤖';
		
		return `
			<div class="result-card">
				<div class="result-header">
					<div class="result-title">${icon} ${label}</div>
					<span class="result-badge badge-loading" id="badge-${id}">⏳ 等待中</span>
				</div>
				<div class="result-content muted" id="out-${id}">等待结果...</div>
				<div class="result-footer" id="footer-${id}" style="display:none;"></div>
			</div>
		`;
	}).join('');

	// 点击运行后自动滚动到页面底部
	requestAnimationFrame(() => {
		window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'smooth' });
	});

	const fd = new FormData();
	fd.append('file', f);
	fd.append('prompt', prompt);

	// 提取所有模型 ID 并作为逗号分隔的字符串发送
	const modelIds = selected.map(v => v.split(':')[1]).join(',');
	console.log('Selected models:', selected);
	console.log('Sending model_ids:', modelIds);
	fd.append('model_ids', modelIds);

	try {
		const res = await fetch(API_BASE + '/compare', { method: 'POST', body: fd });
		if (!res.ok) {
			const errorData = await res.json().catch(() => ({}));
			throw new Error(errorData.detail || `HTTP ${res.status}`);
		}
		const data = await res.json();

		// 更新结果
		if (data.results) {
			let successCount = 0;
			let errorCount = 0;

			Object.keys(data.results).forEach(modelId => {
				const result = data.results[modelId];
				const outEl = $(`#out-${modelId}`);
				const badgeEl = $(`#badge-${modelId}`);
				const footerEl = $(`#footer-${modelId}`);
				
				if (outEl) {
					if (result.ok) {
						outEl.textContent = result.text;
						outEl.classList.remove('muted');
						badgeEl.textContent = '✅ 成功';
						badgeEl.className = 'result-badge badge-success';
						successCount++;
					} else {
						outEl.textContent = result.error || '错误';
						outEl.style.color = 'var(--error-color)';
						badgeEl.textContent = '❌ 失败';
						badgeEl.className = 'result-badge badge-error';
						errorCount++;
					}
					
					// 显示模型版本和耗时
					const footerParts = [];
					if (result.model) {
						footerParts.push(`📦 模型: ${result.model}`);
					}
					if (result.elapsed_ms) {
						footerParts.push(`⏱️ 耗时: ${result.elapsed_ms} ms`);
					}
					if (footerParts.length > 0) {
						footerEl.textContent = footerParts.join(' | ');
						footerEl.style.display = 'block';
					}
				}
			});

			status.textContent = `✨ 完成！成功: ${successCount}, 失败: ${errorCount}`;
			status.style.color = successCount > 0 ? 'var(--success-color)' : 'var(--error-color)';
		}
	} catch (e) {
		console.error('请求失败:', e);
		status.textContent = `❌ 错误: ${e.message}`;
		status.style.color = 'var(--error-color)';
		alert('❌ 请求失败: ' + e.message);
	} finally {
		runBtn.disabled = false;
	}
};

// 页面加载时自动加载一次模型列表
loadModels();

