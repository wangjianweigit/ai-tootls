// 历史记录管理
const API_BASE = '/ai-model-compare';
let currentHistoryId = null;

// 加载历史记录列表
async function loadList() {
	const listContainer = document.getElementById('list');
	
	try {
		const res = await fetch(API_BASE + '/history');
		const data = await res.json();
		
		if (!data.items || data.items.length === 0) {
			listContainer.innerHTML = `
				<div class="empty-state">
					<span class="icon">📭</span>
					<p>暂无历史记录</p>
				</div>
			`;
			return;
		}
		
		// 渲染列表项
		listContainer.innerHTML = data.items.map(item => `
			<div class="history-item" data-id="${item.id}" onclick="viewHistory(${item.id})">
				<div class="item-header">
					<span class="item-id">#${item.id}</span>
					<span class="item-time">${formatTime(item.created_at)}</span>
				</div>
				<div class="item-filename" title="${item.filename || '无文件名'}">
					${item.filename || '无文件名'}
				</div>
			</div>
		`).join('');
		
	} catch (error) {
		console.error('加载历史记录失败:', error);
		listContainer.innerHTML = `
			<div class="empty-state">
				<span class="icon">⚠️</span>
				<p>加载失败，请重试</p>
			</div>
		`;
	}
}

// 查看历史记录详情
async function viewHistory(id) {
	currentHistoryId = id;
	
	// 高亮当前选中项
	document.querySelectorAll('.history-item').forEach(item => {
		item.classList.remove('active');
	});
	const selectedItem = document.querySelector(`.history-item[data-id="${id}"]`);
	if (selectedItem) {
		selectedItem.classList.add('active');
	}
	
	const detailContainer = document.getElementById('detail');
	const imageSection = document.getElementById('image-section');
	const previewImage = document.getElementById('preview');
	
	// 显示加载状态
	detailContainer.innerHTML = `
		<div class="loading-state">
			<div class="spinner"></div>
			<span>加载中...</span>
		</div>
	`;
	
	try {
		const res = await fetch(`${API_BASE}/history/${id}`);
		const data = await res.json();
		
		console.log('获取到的历史数据:', data);
		
		// 显示图片预览
		imageSection.style.display = 'flex';
		previewImage.src = `${API_BASE}/history/${id}/image`;
		
		// 渲染详细信息
		detailContainer.innerHTML = renderDetail(data);
		
	} catch (error) {
		console.error('加载详情失败:', error);
		imageSection.style.display = 'none';
		detailContainer.innerHTML = `
			<div class="empty-state">
				<span class="icon">❌</span>
				<p>加载失败: ${error.message}</p>
			</div>
		`;
	}
}

// 渲染详情内容
function renderDetail(data) {
	const results = [];
	
	// 优先使用新的 results_json 字段（支持多模型）
	if (data.results_json) {
		try {
			let allResults;
			if (typeof data.results_json === 'string') {
				const jsonStr = data.results_json
					.replace(/'/g, '"')
					.replace(/True/g, 'true')
					.replace(/False/g, 'false')
					.replace(/None/g, 'null');
				allResults = JSON.parse(jsonStr);
			} else {
				allResults = data.results_json;
			}
			
			// allResults 是一个对象，key 是 model_id，value 是结果
			for (const [modelId, result] of Object.entries(allResults)) {
				results.push(result);
			}
		} catch (e) {
			console.error('解析 results_json 失败:', e, data.results_json);
		}
	} else {
		// 回退到旧的按 provider 分组的字段（向后兼容）
		if (data.kimi_json) {
			try {
				let kimiData;
				if (typeof data.kimi_json === 'string') {
					const jsonStr = data.kimi_json
						.replace(/'/g, '"')
						.replace(/True/g, 'true')
						.replace(/False/g, 'false')
						.replace(/None/g, 'null');
					kimiData = JSON.parse(jsonStr);
				} else {
					kimiData = data.kimi_json;
				}
				results.push({ provider: 'Kimi', ...kimiData });
			} catch (e) {
				console.error('解析 Kimi 结果失败:', e, data.kimi_json);
			}
		}
		
		if (data.qwen_json) {
			try {
				let qwenData;
				if (typeof data.qwen_json === 'string') {
					const jsonStr = data.qwen_json
						.replace(/'/g, '"')
						.replace(/True/g, 'true')
						.replace(/False/g, 'false')
						.replace(/None/g, 'null');
					qwenData = JSON.parse(jsonStr);
				} else {
					qwenData = data.qwen_json;
				}
				results.push({ provider: 'Qwen', ...qwenData });
			} catch (e) {
				console.error('解析 Qwen 结果失败:', e, data.qwen_json);
			}
		}
		
		if (data.doubao_json) {
			try {
				let doubaoData;
				if (typeof data.doubao_json === 'string') {
					const jsonStr = data.doubao_json
						.replace(/'/g, '"')
						.replace(/True/g, 'true')
						.replace(/False/g, 'false')
						.replace(/None/g, 'null');
					doubaoData = JSON.parse(jsonStr);
				} else {
					doubaoData = data.doubao_json;
				}
				results.push({ provider: 'Doubao', ...doubaoData });
			} catch (e) {
				console.error('解析 Doubao 结果失败:', e, data.doubao_json);
			}
		}
	}
	
	console.log('解析到的结果数量:', results.length, results);
	
	return `
		<div class="detail-info">
			<!-- 上方：基本信息（紧凑） -->
			<div class="detail-header">
				<div class="basic-info-compact">
					<div class="info-item-compact">
						<span class="info-item-label">记录 ID:</span>
						<span class="info-item-value">#${data.id}</span>
					</div>
					<div class="info-item-compact">
						<span class="info-item-label">创建时间:</span>
						<span class="info-item-value">${formatTime(data.created_at)}</span>
					</div>
					<div class="info-item-compact">
						<span class="info-item-label">文件名:</span>
						<span class="info-item-value">${data.filename || '无'}</span>
					</div>
					<div class="info-item-compact">
						<span class="info-item-label">用户提示:</span>
						<span class="info-item-value">${data.prompt || '无'}</span>
					</div>
				</div>
			</div>
			
			<!-- 下方：模型对比结果（主要内容） -->
			<div class="results-section">
				<h3>🤖 模型对比结果</h3>
				${results.map(result => renderResult(result)).join('')}
				${results.length === 0 ? '<div style="color: var(--text-muted); padding: 40px 20px; text-align: center; background: var(--bg-color); border-radius: var(--radius); border: 1px dashed var(--border-color);">暂无模型结果</div>' : ''}
			</div>
		</div>
	`;
}

// 渲染单个结果
function renderResult(result) {
	const isOk = result.ok === true || result.ok === 1;
	const statusClass = isOk ? 'status-ok' : 'status-error';
	const statusText = isOk ? '✓ 成功' : '✗ 失败';
	
	// 构建标题：provider/label + model version
	const providerName = result.provider || result.label || '未知';
	const modelVersion = result.model || result.label || '';
	const titleText = modelVersion && modelVersion !== providerName 
		? `${providerName} (${modelVersion})`
		: providerName;
	
	return `
		<div class="result-block">
			<div class="result-header">
				<div class="result-title-wrapper">
					<span class="result-title">${titleText}</span>
					${result.model ? `<span class="result-model-badge">📦 ${result.model}</span>` : ''}
				</div>
				<div class="result-meta">
					${result.elapsed_ms ? `<span class="result-time">⏱️ ${result.elapsed_ms}ms</span>` : ''}
					<span class="result-status ${statusClass}">${statusText}</span>
				</div>
			</div>
			<div class="result-text">${isOk ? (result.text || '无内容') : (result.error || '未知错误')}</div>
		</div>
	`;
}

// 格式化时间 - 完整日期时间格式
function formatTime(timestamp) {
	if (!timestamp) return '未知时间';
	
	try {
		const date = new Date(timestamp);
		
		// 格式化为: MM-DD HH:mm
		const month = String(date.getMonth() + 1).padStart(2, '0');
		const day = String(date.getDate()).padStart(2, '0');
		const hours = String(date.getHours()).padStart(2, '0');
		const minutes = String(date.getMinutes()).padStart(2, '0');
		
		return `${month}-${day} ${hours}:${minutes}`;
	} catch (e) {
		return timestamp;
	}
}

// 刷新列表
function refreshList() {
	currentHistoryId = null;
	
	// 隐藏详情
	document.getElementById('detail').innerHTML = `
		<div class="empty-state">
			<span class="icon">👈</span>
			<p>请从左侧选择一条记录查看详情</p>
		</div>
	`;
	document.getElementById('image-section').style.display = 'none';
	
	// 重新加载列表
	loadList();
}

// 图片放大功能
function setupImageModal() {
	const modal = document.getElementById('imageModal');
	const modalImage = document.getElementById('modalImage');
	const previewImage = document.getElementById('preview');
	const closeBtn = document.querySelector('.image-modal-close');
	
	// 点击预览图片放大
	if (previewImage) {
		previewImage.addEventListener('click', () => {
			modal.classList.add('active');
			modalImage.src = previewImage.src;
		});
	}
	
	// 点击关闭按钮
	if (closeBtn) {
		closeBtn.addEventListener('click', (e) => {
			e.stopPropagation();
			modal.classList.remove('active');
		});
	}
	
	// 点击模态框背景关闭
	if (modal) {
		modal.addEventListener('click', () => {
			modal.classList.remove('active');
		});
	}
	
	// 点击图片不关闭
	if (modalImage) {
		modalImage.addEventListener('click', (e) => {
			e.stopPropagation();
		});
	}
	
	// ESC 键关闭
	document.addEventListener('keydown', (e) => {
		if (e.key === 'Escape' && modal.classList.contains('active')) {
			modal.classList.remove('active');
		}
	});
}

// 事件监听
document.addEventListener('DOMContentLoaded', () => {
	// 加载初始列表
	loadList();
	
	// 刷新按钮
	const refreshBtn = document.getElementById('refresh-btn');
	if (refreshBtn) {
		refreshBtn.addEventListener('click', refreshList);
	}
	
	// 设置图片放大功能
	setupImageModal();
});

// 导出供 HTML 使用
window.viewHistory = viewHistory;
