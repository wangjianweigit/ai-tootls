// 工具函数
const API_BASE = '/ai-model-compare';
const $ = (selector) => document.querySelector(selector);

// 检查是否为管理员模式
const urlParams = new URLSearchParams(window.location.search);
const isManagerMode = urlParams.get('manager') === 'true';

// 加载模型列表
async function loadModels() {
	const listContainer = $('#list');
	
	// 显示加载状态
	listContainer.innerHTML = `
		<div class="loading-state">
			<div class="spinner"></div>
			<span>加载中...</span>
		</div>
	`;

	try {
		const res = await fetch(API_BASE + '/models');
		if (!res.ok) throw new Error('加载失败');
		
		const data = await res.json();
		const models = data.items || [];

		if (models.length === 0) {
			listContainer.innerHTML = `
				<div class="loading-state">
					<span>暂无模型，请添加新模型</span>
				</div>
			`;
			return;
		}

	// 构建表格
	const rows = models.map(model => {
		const providerIcons = {
			kimi: '🌙',
			qwen: '🧠',
			doubao: '🔥',
			openai: '🤖',
			claude: '💬',
			gemini: '✨'
		};
		const icon = providerIcons[model.provider] || '🔧';
		const enabledBadge = model.enabled
			? '<span class="badge badge-yes">✓ 启用</span>'
			: '<span class="badge badge-no">✗ 禁用</span>';

		return `
			<tr>
				<td>${model.id}</td>
				<td>${icon} ${model.provider.toUpperCase()}</td>
				<td>${model.label || '-'}</td>
				<td>${model.model}</td>
				<td class="table-muted">${model.base_url}</td>
				<td>${enabledBadge}</td>
				${isManagerMode ? `
				<td>
					<button class="btn-toggle" data-id="${model.id}" data-enabled="${model.enabled}">
						${model.enabled ? '禁用' : '启用'}
					</button>
					<button class="btn-delete" data-id="${model.id}">删除</button>
				</td>
				` : ''}
			</tr>
		`;
	}).join('');

	listContainer.innerHTML = `
		<table>
			<thead>
				<tr>
					<th>ID</th>
					<th>Provider</th>
					<th>名称</th>
					<th>模型</th>
					<th>Base URL</th>
					<th>状态</th>
					${isManagerMode ? '<th>操作</th>' : ''}
				</tr>
			</thead>
			<tbody>
				${rows}
			</tbody>
		</table>
	`;

		// 绑定切换启用/禁用按钮事件
		document.querySelectorAll('.btn-toggle').forEach(btn => {
			btn.onclick = async () => {
				const modelId = btn.getAttribute('data-id');
				const isEnabled = btn.getAttribute('data-enabled') === '1';
				
				btn.disabled = true;
				const originalText = btn.textContent;
				btn.textContent = '处理中...';

				try {
					const res = await fetch(`${API_BASE}/models/${modelId}/toggle`, { method: 'PATCH' });
					if (!res.ok) throw new Error('操作失败');
					
					await loadModels();
					showStatus(`✅ 已${isEnabled ? '禁用' : '启用'}模型`, 'success');
				} catch (e) {
					alert('操作失败: ' + e.message);
					btn.disabled = false;
					btn.textContent = originalText;
				}
			};
		});

		// 绑定删除按钮事件
		document.querySelectorAll('.btn-delete').forEach(btn => {
			btn.onclick = async () => {
				const modelId = btn.getAttribute('data-id');
				if (!confirm('确定要删除此模型吗？')) return;

				btn.disabled = true;
				btn.textContent = '删除中...';

				try {
					const res = await fetch(`${API_BASE}/models/${modelId}`, { method: 'DELETE' });
					if (!res.ok) throw new Error('删除失败');
					
					await loadModels();
					showStatus('✅ 删除成功', 'success');
				} catch (e) {
					alert('删除失败: ' + e.message);
					btn.disabled = false;
					btn.textContent = '删除';
				}
			};
		});

	} catch (e) {
		console.error('加载模型列表失败:', e);
		listContainer.innerHTML = `
			<div class="loading-state">
				<span style="color: var(--error-color);">❌ 加载失败: ${e.message}</span>
			</div>
		`;
	}
}

// 显示状态消息
function showStatus(message, type = 'info') {
	const status = $('#status');
	status.textContent = message;
	
	if (type === 'success') {
		status.style.color = 'var(--success-color)';
	} else if (type === 'error') {
		status.style.color = 'var(--error-color)';
	} else {
		status.style.color = 'var(--text-muted)';
	}

	// 3秒后清除状态
	setTimeout(() => {
		status.textContent = '';
	}, 3000);
}

// 清空表单
function clearForm() {
	$('#provider').value = '';
	$('#label').value = '';
	$('#base_url').value = '';
	$('#api_key').value = '';
	$('#model').value = '';
	$('#enabled').checked = true;
}

// 添加模型
$('#create').onclick = async () => {
	const provider = $('#provider').value.trim();
	const label = $('#label').value.trim();
	const baseUrl = $('#base_url').value.trim();
	const apiKey = $('#api_key').value.trim();
	const model = $('#model').value.trim();
	const enabled = $('#enabled').checked;

	// 验证必填字段
	if (!provider) {
		alert('⚠️ 请填写 Provider');
		$('#provider').focus();
		return;
	}

	if (!baseUrl) {
		alert('⚠️ 请填写 Base URL');
		$('#base_url').focus();
		return;
	}

	if (!apiKey) {
		alert('⚠️ 请填写 API Key');
		$('#api_key').focus();
		return;
	}

	if (!model) {
		alert('⚠️ 请填写模型名称');
		$('#model').focus();
		return;
	}

	const createBtn = $('#create');
	createBtn.disabled = true;
	showStatus('⏳ 提交中...', 'info');

	const fd = new FormData();
	fd.append('provider', provider);
	fd.append('label', label);
	fd.append('base_url', baseUrl);
	fd.append('api_key', apiKey);
	fd.append('model', model);
	fd.append('enabled', enabled ? '1' : '0');

	try {
		const res = await fetch(API_BASE + '/models', { method: 'POST', body: fd });
		if (!res.ok) {
			const errorData = await res.json().catch(() => ({}));
			throw new Error(errorData.detail || '创建失败');
		}

		clearForm();
		await loadModels();
		showStatus('✅ 添加成功', 'success');
	} catch (e) {
		console.error('创建模型失败:', e);
		showStatus('❌ ' + e.message, 'error');
		alert('❌ 创建失败: ' + e.message);
	} finally {
		createBtn.disabled = false;
	}
};

// 如果是管理员模式，显示管理功能
if (isManagerMode) {
	document.querySelectorAll('.manager-only').forEach(el => {
		el.style.display = '';
	});
}

// 页面加载时自动加载模型列表
loadModels();

